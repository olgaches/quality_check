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


def knoten_auf_knoten(table_name, environment, output_feedback, field):
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
            dic_data[(row[0], row[2])] = row[1]

    duplicates = []
    for xy, objids in groupby(sorted(dic_data.items(), key=itemgetter(1)), itemgetter(1)):
        all_objids = list(map(itemgetter(0), objids))
        if len(all_objids) > 1:
            output_feedback.writelines(str(all_objids) + ';' + str(xy) + '\n')
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