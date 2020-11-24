# dynamic-template-generator
Python script to convert Elasticsearch explicit mappings to dynamic templates and apply an uppercase or lowercase normaliser to all keyword fields. Applying a case normaliser to all keyword fields is a simple way to set up Elasticsearch to do case in-sensitive search. This is becasue keyword fields are exact match and case sensitive. The normaliser is applied at both search and index time so the operator doesn't need to worry about the case of the string they are searching.

Explicit mappings define each field in the index, even if no data exists. Explicit mappings also take priority over dynamic template rules. Dynamic template are recommended as they only create a field in the index mapping when data to populate the field is indexed by Elasticsearch.
## Motivation
- Beats templates set the explicit mappings which override dynamic templates. 
- The beats templates make heavy use of keyword fields which are case sensitive.
- Operators must remember the case of the string they are searching if no case normaliser is applied to the keyword field.
- Security use-cases require case in-sensitive search to make sure all logs are found during incident response.
- Beats sets mappings for all possible fields which pollutes index patterns.
- Kibana struggles to create generic index patterns if too many fields exist in the target index mappings.
- Reduce the list of suggested fields when creating Kibana visuals, Discover filters, Data Transforms etc.

## Requirements
Dynamic template generator requires python 3.4+

## Usage
Run the script once to create the current_template and new_template folders.

### current_templates folder
The following example shows how to load templates from the default dynamic-template-generator\current_templates folder. The new templates will be saved in the dynamic-template-generator\new_templates folder.
```
python3 dynamic-template-generator.py -n lowercase -d
```

### Specify a file
Specify an input and output template file. If no output file is specified, the template will be saved in the dynamic-template-generator\new_templates folder.
```
python3 dynamic-template-generator.py -f INPUT_FILEPATH -o OUTPUT_FILEPATH -n uppercase -d
```

### Generate dynamic templates
Set the -d or --dynamic parameter to generate dynamic templates from explict index mappings. 
Explicit mappings which override dynamic templates are deleted from the new template.
```
python3 dynamic-template-generator.py -d
```

### Generate dynamic templates and apply a case normaliser
The -n and --normaliser parameter accepts uppercase or lowercase. The case normaliser is applied to all keyword fields in the mapping. The dynamic template is generated when the -d or --dynamic parameter is set.
```
python3 dynamic-template-generator.py -d -n lowercase
```

### Apply a case normaliser
Apply the case normaliser to the explicit mapping and dynamic templates, without generating new dynamic templates from the explicit mappings.
```
python3 dynamic-template-generator.py -n lowercase
```

### Set the refresh interval to 60 seconds and enable best compression
Set simple settings like the refresh interval and the best-compression codec.
```
python3 dynamic-template-generator.py -d -n lowercase -c -r 60
```

## Options
```
  -h, --help            show this help message and exit
  -f, --filepath        Input template filepath. Defaults to all files in the current_templates folder.
  -o, --output          Output template filepath. Defaults to all files in the new_templates folder.
  -n, --normaliser      Upper or lowercase normaliser. Set to uppercase or lowercase.
  -d, --dynamic         Convert mappings to dynamic templates.
  -c, --compression     Enable best compression.
  -r, --refresh         Set the refresh interval seconds.
```

