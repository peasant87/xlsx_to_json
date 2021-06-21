# xlsx_to_json

### Before running the script
This script needs some libraries not included with Python to run succesfully.

Run the command below to install this libraries.
```
pip install -r requirements.txt
```
***IMPORTANT: Columns in the xlsx file starting with "#" will be ignored.***
<br>

### Running
- To run the script, use a command similar to the one below
```
python xlsx_to_json.py path_to_file
```
- To run the script, using a file with the data type at second row run a command similitar to the below
```
python xlsx_to_json.py path_to_file --header_rows=2
```

### Output
This script save the files to a folder named "output_json", in the same folder where the script is in.

Inside this folder are the files for the products, with the pattern: 
```
name_id.json
```
