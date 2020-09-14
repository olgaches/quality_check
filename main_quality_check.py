"""
Created on 14.09.2020
@author: KOO
The script checks how many user-defined extensions are there in the client's database, and if these extensions are still used.
"""

import codecs
import os
from arcpy import env
from functions import table_check
from functions import check_media_folder

rootdir = "C:/data/SEW_Yverdon/SEW_Yverdon/"
env.workspace = rootdir + "datasources/SEW_Yverdon_FGDB/db/SEW_Yverdon_FGDB.gdb/"

media_folder = rootdir + "media/sew"
output_file = os.path.join(rootdir, 'feedback.txt')
output_feedback = codecs.open(output_file, 'w', 'utf-8')

media_check = check_media_folder(media_folder, output_feedback)

GN_lookup_check = table_check('GN_lookup', 'lookup_table', output_feedback)
GNREL_formula_check = table_check('GNREL_FORMULA', 'FORMULA', output_feedback)