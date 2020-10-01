"""
Created on 14.09.2020
@author: KOO
"""

import arcpy
from arcpy import env
import fnmatch
import os
import codecs
from itertools import groupby
from operator import itemgetter

def check_media_folder(media_folder, client_defined_tables_columns, output_feedback, environment):
    """checks if any of the user-defined tables or columns appears in the media folder. XML files that have
    '_update' in their name are not taken into account"""

    env.workspace = environment
    client_defined_tables_media = []
    for dirpath, dirs, files in os.walk(media_folder):
        for filename in fnmatch.filter(files, '*.xml'):
            with codecs.open(os.path.join(dirpath, filename)) as text_file:
                lines = text_file.readlines()
                lines = str(lines)
                for table_column_name in client_defined_tables_columns:
                    if table_column_name.lower() in lines.lower():
                        if '_update' not in filename:
                            print filename, table_column_name
                            client_defined_tables_media.append(table_column_name)

    output_feedback.writelines('Number of user-defined tables or columns appearing in the folder "media" is: ' + str(
        len(set(client_defined_tables_media))) + '\n')
    output_feedback.writelines('Names of user-defined tables or columns appearing in the folder "media" are: ' + str(
        set(client_defined_tables_media)) + '\n')
    return


def table_check(table_name, column_name, output_feedback, environment):
    """checks if any user-defined tables or columns appear in the table given as input (table_name)"""
    env.workspace = environment
    table = environment + '/' + table_name
    cursor = arcpy.da.SearchCursor(table, column_name)

    client_defined = []
    for row in cursor:
        if 'u_' in str(row).lower():
            client_defined.append(row)
    output_feedback.writelines(
        'Number of user-defined tables or columns appearing in %s' % (table_name) + ': ' + str(len(client_defined)) + '\n')
    output_feedback.writelines(
        'Names of user-defined tables or columns appearing in %s' % (table_name) + ': ' + str(client_defined) + '\n')
    return


def columns_check(output_feedback, environment, to_check_expression):
    """checks if there are any user-defined columns in the environment defined as env.workspace
    A check-expression can be for example 'u_', '_old', '_1', etc."""

    env.workspace = environment

    def columns(table):
        all_fields = arcpy.ListFields(table)
        for field in all_fields:
            if to_check_expression in str(field.name).lower():
                values = [row[0] for row in arcpy.da.SearchCursor(table, field.name)]
                if len(values) == 0 or str(set(values)) == 'set([None])':
                    output_feedback.writelines('column %s of the table %s is empty' % (field.name, table) + '\n')
                else:
                    output_feedback.writelines(
                        'column %s of the table %s has the following unique values: ' % (field.name, table) + str(set(values)) + '\n')
        return

    output_feedback.writelines('**The following is the check of the user-defined columns in the database (%s) **' % (to_check_expression) + '\n')

    tables = arcpy.ListTables()
    for table in tables:
        columns(table)

    datasets = arcpy.ListDatasets()
    for dataset in datasets:
        env.workspace = environment + dataset
        features = arcpy.ListFeatureClasses()
        for feature in features:
            columns(feature)

    return


def knoten_auf_knoten(table_name, environment, output_feedback, field, ndigit):
    """checks if there are any geometrically overlapping points. For tables in the datasets the names of the dataset
    has to be given in the environment, e.g. 'SEW/AWK_ABWASSERKNOTEN', field variable is the field that should be additionally checked,
    for example ART_BAUWERK in AWK_ABWASSERKNOTEN"""
    env.workspace = environment
    table = environment + '/' + table_name
    output_feedback.writelines(
        '**The following is the check if there are any geometrically overlapping points in %s**: ' % (table_name) + '\n')

    dic_data = {}
    with arcpy.da.SearchCursor(table, ['OID@', 'SHAPE@XY', field]) as rows:
        for row in rows:
            x = round(row[1][0], ndigit)
            y = round(row[1][1], ndigit)
            dic_data[(row[0], row[2])] = (x, y)
    del rows

    duplicates = []
    for xy, objids in groupby(sorted(dic_data.items(), key=itemgetter(1)), itemgetter(1)):
        all_objids = list(map(itemgetter(0), objids))
        if len(all_objids) > 1:
            output_feedback.writelines(str(xy[0]) + ';' + str(xy[1]) + ';')
            count = 1
            for i in all_objids:
                output_feedback.writelines(str(i[0]) + ';' + str(i[1]))
                if count < len(all_objids):
                    output_feedback.writelines(';')
                    count = count + 1
            output_feedback.writelines('\n')
            duplicates.append(all_objids)
    print len(duplicates)
    output_feedback.writelines('Number of duplicates in %s: ' % (table_name) + str(len(duplicates)) + '\n')
    return

def linie_auf_linie(table_name, environment, output_feedback):
    """checks if there are any geometrically overlapping lines. For tables in the datasets the names of the dataset
    has to be given in the environment, e.g. 'SEW/AWK_HALTUNG'"""
    env.workspace = environment
    table = environment + '/' + table_name
    output_feedback.writelines('**The following is the check if there are any geometrically overlapping lines in %s**: ' % (table_name) + '\n')

    dic_data = {}
    with arcpy.da.SearchCursor(table, ['OID@', 'SHAPE@WKT']) as rows:
        for row in rows:
            dic_data[row[0]] = row[1]

    duplicates = []
    for xy, objids in groupby(sorted(dic_data.items(), key=itemgetter(1)), itemgetter(1)):
        all_objids = list(map(itemgetter(0), objids))
        if len(all_objids) > 1:
            output_feedback.writelines(str(all_objids) + ';' + str(xy) + '\n')
            duplicates.append(all_objids)
    print len(duplicates)
    output_feedback.writelines('Number of duplicates in %s: ' % (table_name) + str(len(duplicates)) + '\n')
    return

def unterschiedliche_knoten(environment):
    """Checks if the counts and references of different types of BAUWERK are correct"""
    env.workspace = environment
    table_abwasserknoten = environment + '/SEW/AWK_ABWASSERKNOTEN'
    table_abwasserbauwerk = environment + '/SEW/AWK_ABWASSERBAUWERK'
    print 'Alle Abwasserknoten: ', arcpy.GetCount_management(table_abwasserknoten)
    print 'Alle Abwasserbauwerk: ', arcpy.GetCount_management(table_abwasserbauwerk)

    field_zusatztabelle = 'KNOTEN_REF'
    field_abwasserknoten = ['globalid']
    tables = [('/AWK_VERSICKERUNGSANLAGE',2),('/AWK_VORFLUTEREINLAUF',3),('/AWK_ARABAUWERK',4),('/AWK_ABSPDROSSELORGAN',8),('/AWK_UEBERLAUF',9),('/AWK_EINLAUF',10),('/AWK_ANSCHLUSSPUNKT',11),('/AWK_PUMPE',12),('/AWK_PUMPWERK',13),('/AWK_BECKEN',14)]
    for entry in tables:
        table = environment + entry[0]
        where = '"ART_BAUWERK" = %s' % entry[1]
        abwasserknoten_result = [row[0] for row in arcpy.da.SearchCursor(table_abwasserknoten, field_abwasserknoten, where)]
        tabelle_selber_result = [row[0] for row in arcpy.da.SearchCursor(table, field_zusatztabelle)]
        count_abwasserknoten = len([row[0] for row in arcpy.da.SearchCursor(table_abwasserknoten, ['ART_BAUWERK'], where)])
        count_tabelle_selber = int(arcpy.GetCount_management(table).getOutput(0))
        if set(abwasserknoten_result) == set(tabelle_selber_result) and len(abwasserknoten_result) == len(tabelle_selber_result):
            print str(entry[0][5:]).title(), 'the references are correct', count_abwasserknoten, count_tabelle_selber
        else:
            print str(entry[0][5:]).title(), 'counts or references are not correct', count_abwasserknoten, count_tabelle_selber

    subtypen = [('Unbekannt',0),('Normschacht',1),('Spezialbauwerk',6),('Leitungspunkt',7)]
    for i in subtypen:
        where = '"ART_BAUWERK" = %s' % i[1]
        abwasserknoten_result_link = [row[0] for row in arcpy.da.SearchCursor(table_abwasserknoten, ['BAUWERK_REF'], where)]
        abwasserbauwerk_result_link = [row[0] for row in arcpy.da.SearchCursor(table_abwasserbauwerk, ['globalid'], where)]
        abwasserknoten_result = len([row[0] for row in arcpy.da.SearchCursor(table_abwasserknoten, ['ART_BAUWERK'], where)])
        abwasserbauwerk_result= len([row[0] for row in arcpy.da.SearchCursor(table_abwasserbauwerk, ['ART_BAUWERK'], where)])
        if set(abwasserknoten_result_link) == set(abwasserbauwerk_result_link) and len(abwasserknoten_result) == len(
                abwasserbauwerk_result):
            print i[0], 'the references are correct', abwasserknoten_result, abwasserbauwerk_result
        else:
            print i[0], 'counts or references are not correct', abwasserknoten_result, abwasserbauwerk_result
    return

def kanal_ohne_haltung(environment):
    """Checks if there are Kanaele, that do not have any Haltung"""
    env.workspace = environment
    haltungen = environment + "SEW/AWK_HALTUNG"
    kanal_ref= []
    with arcpy.da.SearchCursor(haltungen, ['KANAL_REF']) as rows:
        for row in rows:
            kanal_ref.append(row[0])
    del rows

    kanal = environment + "SEW/AWK_KANAL"
    global_id_kanal = []
    with arcpy.da.SearchCursor(kanal, ['OID@', 'globalid']) as rows:
        for row in rows:
            global_id_kanal.append(row[1])
            if row[1] not in kanal_ref:
                print row[0]
    print len(global_id_kanal)
    for i in set(kanal_ref).difference(set(global_id_kanal)):
        print i
    del rows
    return



def abwasserknoten_haltungen(environment):
    """TO FIX!!!!!"""
    env.workspace = environment

    abwasserknoten_layer = environment + "SEW/AWK_ABWASSERKNOTEN"
    print arcpy.GetCount_management(abwasserknoten_layer)
    arcpy.MakeFeatureLayer_management(abwasserknoten_layer, "AWK_ABWASSERKNOTEN_lyr")
    # arcpy.SelectLayerByAttribute(abwasserknoten_layer, "NEW_SELECTION", 'OBJECTID<1000')
    # arcpy.CopyFeatures_management("AWK_ABWASSERKNOTEN_lyr", "in_memory\\AWK_ABWASSERKNOTEN_Ohne_Haltungen")

    abwasserknoten_objid = []
    with arcpy.da.SearchCursor(abwasserknoten_layer, ['OID@']) as rows:
        for row in rows:
            abwasserknoten_objid.append(row)
    del rows

    haltungen_layer = environment + "SEW/AWK_HALTUNG"
    arcpy.MakeFeatureLayer_management(haltungen_layer, "AWK_HALTUNG_lyr")
    arcpy.Buffer_analysis("AWK_HALTUNG_lyr", "in_memory\\AWK_HALTUNG_lyr_buffer", "2 Meters")
    arcpy.ErasePoint_edit(abwasserknoten_layer, "in_memory\\AWK_HALTUNG_lyr_buffer", 'INSIDE')

    abwasserknoten_objid2 = []
    with arcpy.da.SearchCursor(abwasserknoten_layer, ['OID@']) as rows2:
        for row in rows2:
            abwasserknoten_objid2.append(row)
    del rows2

    for i in set(abwasserknoten_objid2).difference(set(abwasserknoten_objid)):
        print i
    return

def knoten_ohne_aufbruch(environment):
    """To FIX: Knoten, die die Haltung nicht aufbrechen"""
    env.workspace = environment


    haltungen_layer = environment + "SEW/AWK_HALTUNG"
    arcpy.MakeFeatureLayer_management(haltungen_layer, "AWK_HALTUNG_lyr")

    abwasserknoten_layer = environment + "SEW/AWK_ABWASSERKNOTEN"
    arcpy.MakeFeatureLayer_management(abwasserknoten_layer, "AWK_ABWASSERKNOTEN_lyr")

    arcpy.FeatureVerticesToPoints_management("AWK_HALTUNG_lyr", "in_memory\\AWK_HALTUNG_lyr_knoten", "BOTH_ENDS")
    arcpy.Buffer_analysis("in_memory\\AWK_HALTUNG_lyr_knoten", "in_memory\\AWK_HALTUNG_lyr_knoten_buffer", "1 Meters")
    #arcpy.ErasePoint_edit(abwasserknoten_layer, "AWK_HALTUNG_lyr_knoten_buffer", 'INSIDE')
    #arcpy.SpatialJoin("in_memory\\AWK_HALTUNG_lyr_knoten_buffer", abwasserknoten_layer, "AWK_HALTUNG_spatial_join")

    with arcpy.da.SearchCursor("AWK_HALTUNG_spatial_join", ['OID@, JOIN']) as rows:
        for row in rows:
            if row[1] == 0:
                print row[0]
    del rows
    return
