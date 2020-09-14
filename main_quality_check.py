"""
Created on 14.09.2020
@author: KOO
The script checks how many user-defined extensions are there in the client's database, and if these extensions are still used.
Be aware, the code is not particularly efficient, for an SEW solution you need ca. 5 minutes for each: media check
and columns check. The tables check is very fast.
"""

import codecs
import os
import time
import arcpy
from arcpy import env
import re
from functions import table_check
from functions import check_media_folder
from functions import columns_check

rootdir = "C:/data/SEW_Yverdon/SEW_Yverdon/"
database_path = rootdir + "datasources/SEW_Yverdon_FGDB/db/SEW_Yverdon_FGDB.gdb/"

media_folder = rootdir + "media/sew"
output_file = os.path.join(rootdir, 'feedback.txt')
output_feedback = codecs.open(output_file, 'w', 'utf-8')

##--------------beginning general characteristics--------------
##checks how many user-defined tables and columns are in the database, and how many of the tables are secondary tables
env.workspace = database_path
tables = arcpy.ListTables()

pattern = 'U_[A-Z]{3}S'

client_defined_tables = []
client_defined_lookup_tables = []
client_defined_fields = []
for table in tables:
    if 'u_' in table.lower():
        client_defined_tables.append(table)
        if re.match(pattern, table):
            client_defined_lookup_tables.append(table)
    all_fields = arcpy.ListFields(table)
    for field in all_fields:
        if 'u_' in str(field.name).lower():
            client_defined_fields.append(field.name)

datasets = arcpy.ListDatasets()
for dataset in datasets:
    env.workspace = database_path + dataset
    features = arcpy.ListFeatureClasses()
    for table in features:
        if 'u_' in table.lower():
            client_defined_tables.append(table)
            if re.match(pattern, table):
                client_defined_lookup_tables.append(table)
        all_fields = arcpy.ListFields(table)
        for field in all_fields:
            if 'u_' in str(field.name).lower():
                client_defined_fields.append(field.name)

output_feedback.writelines('Number of user-defined tables is: ' + str(len(client_defined_tables)) + '\n')
output_feedback.writelines(
    'Names of the user-defined tables are the following: ' + str(client_defined_tables) + '\n')

output_feedback.writelines(
    'Number of user-defined look up tables is: ' + str(len(client_defined_lookup_tables)) + '\n')
output_feedback.writelines(
    'Names of the user-defined look up tables are the following: ' + str(client_defined_lookup_tables) + '\n')

client_defined_fields_set = set(client_defined_fields)

output_feedback.writelines(
    'Number of user-defined columns is: ' + str(len(client_defined_fields_set)) + '\n')
output_feedback.writelines(
    'Names of the user-defined columns are the following: ' + str(client_defined_fields_set) + '\n')

##--------------end general characteristics--------------

##--------------beginning functions--------------
start_time = time.time()

GN_lookup_check = table_check('GN_lookup', 'lookup_table', output_feedback, database_path)

GNREL_formula_check = table_check('GNREL_FORMULA', 'FORMULA', output_feedback, database_path)

client_defined_fields_tables = client_defined_fields_set.union(set(client_defined_tables))
print 'Length of the set for the media folder check', len(client_defined_fields_tables)

##--------------longer processes, comment out if not needed--------------
media_check = check_media_folder(media_folder, client_defined_fields_tables, output_feedback, database_path)
elapsed_time = time.time() - start_time
print 'Time after media_check', time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

result_column_check = columns_check(output_feedback, database_path)
elapsed_time = time.time() - start_time
print 'Time after column_check', time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

##--------------end functions--------------



