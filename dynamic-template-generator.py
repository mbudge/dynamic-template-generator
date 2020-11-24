#!/usr/bin/python3

# Author Matthew Budge <https://github.com/mbudge>
# Copyright 2020 Matthew Budge
# License GNU GENERAL PUBLIC LICENSE
# Git https://github.com/mbudge/dynamic-template-generator

import sys
import os
import json
import argparse
from pathlib import Path

current_path = os.path.dirname(os.path.realpath(__file__))
current_templates_path = os.path.join(current_path, "current_templates")
new_templates_path = os.path.join(current_path, "new_templates")

# Get the full file paths for the templates in the current_templates folder.
def load_templates():
    try:
        filepaths = []
        current_path = os.path.dirname(os.path.realpath(__file__))
        default_templates_path = os.path.join(current_path, "current_templates")
        for root, names, files in os.walk(default_templates_path):
            for filename in files:
                new = os.path.join(default_templates_path, filename)
                if new not in filepaths:
                    filepaths.append(new)
        return filepaths
    except Exception as err:
        print("Error, Error loading template file paths from the current_templates folder: {0}".format(str(err)))
        sys.exit(1)

# Apply the case normaliser to the index mapping to create case in-sensitive search.
# This is done through function recursion.
def add_case_normalizer(mappings, case):
    try:
        for k, v in list(mappings.items()):
            if isinstance(k, str) and isinstance(v, str):
                if k.lower().strip() == "type" and v.lower().strip() == "keyword":
                    # The normaliser is applied to all keyword fields.
                    mappings["normalizer"] = case
            elif isinstance(k, str) and isinstance(v, dict):
                # The add case normaliser function is called when a new object in the mapping is found.
                add_case_normalizer(v, case)
            else:
                pass
    except Exception as err:
        print("Error, Add case normaliser: {0}".format(str(err)))
        sys.exit(1)

# Apply the case normaliser to the index mapping's existing dynamic templates to create case in-sensitive search.
# This is done through function recursion.
def add_case_normalizer_to_dynamic_templates(dynamic_templates, case):
    try:
        for d in dynamic_templates:
            for k, v in list(d.items()):
                if isinstance(k, str) and isinstance(v, str):
                    if k.lower().strip() == "type" and v.lower().strip() == "keyword":
                        # The normaliser is applied to all keyword fields.
                        d["normalizer"] = case
                elif isinstance(k, str) and isinstance(v, dict):
                    # The add case normaliser function is called when a new object in the dynamic template is found.
                    add_case_normalizer(v, case)
                else:
                    pass
    except Exception as err:
        print("Error, Add case normaliser to dynamic templates: {0}".format(str(err)))
        sys.exit(1)

# Function to crreate dynamic templates from explicit mappings.
# The fields will only be created in the Elasticsearch index if they exist.
def create_dynamic_templates_from_mappings(path, key, data):
    try:

        # New dynamic template.
        new = {}

        # Path is None when processing fields at the top level i.e. @timestamp
        # Not fields in objects i.e. The created field in the event object. The path for this would be event.created
        if path is None:
            # The dynamic template name is the fields path.
            name = key
            # The path gets updated.
            path = name
        else:
            # The dynamic template name is the fields path.
            # Fields in the object are used to build the dynamic template name.
            name = path.strip(".") + "." + key
            # The path gets updated so child objects can add their fields.
            path = name


        new[name] = {}
        # The name is the path.
        # Use path_match so the dynamic template matches on the exact path.
        new[name]["path_match"] = name

        # if "type" in data and data["type"] == "keyword":
        #     data["normalizer"] = "lowercase"

        # When properties does not exist, there are no more child objects to process.
        # Add the new dynamic template to the list.
        if "properties" not in data:
            new[name]["mapping"] = data
            new_dynamic_template.append(new)
        else:
            # The object contains multiple fields.
            # Create a dynamic template for each field in the object.
            for k, v in list(data["properties"].items()):
                create_dynamic_templates_from_mappings(path, k, v)

    except Exception as err:
        print("Error, Create dynamic template: {0}".format(str(err)))
        sys.exit(1)


def main(args):
    try:

        # Load the filepaths from command line parameters or the default folder.
        if args.filepath:
            filepaths = [args.filepath]
        else:
            filepaths = load_templates()

        # Warn the user if there's no template files to process.
        if len(filepaths) == 0:
            print("Exiting, No template files to process")
            sys.exit(1)

        # Process the templates.
        for filepath in filepaths:

            print("Processing: {0}".format(filepath))

            # Make sure the new_dynamic_template global variable is empty when processing a new template.
            global new_dynamic_template
            new_dynamic_template = []

            filename = Path(filepath).name
            # input_template_path is used when args.output is set to .
            # When args.output is set to . the new template is saved in the same folder as the input template.
            input_template_path = os.path.dirname(filepath)

            try:
                # Open file and read bytes
                f = open(filepath, "rb")
                b = f.read()
                f.close()

                # json load
                template = json.loads(b)

                # Extract the mappings from the index template, component template or legacy template.
                if "template" in template and "mappings" in template["template"]:
                    template_type = "index_or_component"
                    mappings = template["template"]["mappings"]
                elif "mappings" in template:
                    template_type = "legacy"
                    mappings = template["mappings"]
                else:
                    print("Error, Invalid index template: Failed to locate the mappings object")
                    sys.exit(1)

                if "properties" not in mappings:
                    print("Error, Invalid template mapping: The first properties object does not exist.")
                    sys.exit(1)

            except Exception as err:
                print("Error, Error loading template: {0}".format(str(err)))
                sys.exit(1)

            try:
                # Apply the case normaliser.
                # Do this before generating the dynamic templates.
                if args.normaliser:

                    # Apply normaliser to mappings fields and objects.
                    for k, v in list(mappings.items()):
                        if isinstance(k, str) and isinstance(v, dict):
                            add_case_normalizer(v, args.normaliser)

                    # Apply the normaliser to dynamic template fields.
                    if "dynamic_templates" in mappings:
                        add_case_normalizer_to_dynamic_templates(mappings["dynamic_templates"], args.normaliser)
            except Exception as err:
                print("Error, Applying case normaliser: {0}".format(str(err)))
                sys.exit(1)

            try:
                # Convert the mapping to dynamic templates.
                # Do this after adding the case normaliser to keep things simple.
                if args.dynamic:
                    for key, data in list(mappings["properties"].items()):
                        if isinstance(key, str) and isinstance(data, dict):
                            # The path is set to None for fields at the root level.
                            create_dynamic_templates_from_mappings(None, key, data)

                    # Set the dynamic templates if they were generated successfully.
                    if len(new_dynamic_template) > 0:
                        mappings["dynamic_templates"] = new_dynamic_template

                        # Delete the explicit mappings as they will override the dynamic templates.
                        del mappings["properties"]
            except Exception as err:
                print("Error, Converting mapping to dynamic templates: {0}".format(str(err)))
                sys.exit(1)

            try:
                # Some settings require the index.settings object.
                # Make sure this is set in both index and component templates, as well as legacy templates.
                index_settings = {}
                if args.refresh or args.compression:
                    if template_type == "index_or_component":
                        if "settings" not in template["template"]:
                            template["template"]["settings"] = {}
                        if "index" not in template["template"]["settings"]:
                            template["template"]["settings"]["index"] = {}
                        index_settings = template["template"]["settings"]["index"]
                    elif template_type == "legacy":
                        if "settings" not in template:
                            template["settings"] = {}
                        if "index" not in template["settings"]:
                            template["settings"]["index"] = {}
                        index_settings = template["settings"]["index"]

                # Enable best compression.
                if args.compression:
                    index_settings["codec"] = "best_compression"

                # Set the refresh interval.
                if args.refresh:
                    index_settings["refresh_interval"] = "{0}s".format(str(args.refresh))
            except Exception as err:
                print("Error, Applying index settings: {0}".format(str(err)))
                sys.exit(1)

            try:
                # Write to output file.
                if args.output and args.output == ".":
                    action = input("Overwrite input template: yes/no ").lower().strip()
                    if action == "yes":
                        # Write to the same directory and the input file.
                        output_path = os.path.join(input_template_path, filename)
                    else:
                        # Write to the same directory and the input file.
                        output_path = os.path.join(input_template_path, "new-{0}".format(filename))
                elif args.output:
                    # Write to the file path specified at the command line parameters.
                    output_path = args.output
                else:
                    # Write to the new_templates folder.
                    output_path = os.path.join(new_templates_path, filename)

                if output_path.lower().strip() == filepath.lower().strip():
                    action = input("Overwrite input template: yes/no ").lower().strip()
                    if not action == "yes":
                        print("Exiting, The input template was not overwritten. Specify a new output file location.")
                        sys.exit(0)

                print("Output file: {0}".format(output_path))

                # Json encode.
                j = json.dumps(template, indent=2, sort_keys=True)

                # Write to file.
                f = open(output_path, "w")
                f.write(j)
                f.close()
            except Exception as err:
                print("Error, Writing output file: {0}".format(str(err)))
                sys.exit(1)

    except Exception as err:
        print("Error, Dynamic template generator error: {0}".format(str(err)))
        sys.exit(1)


if __name__ == "__main__":

    # Make sure these folders exist.
    Path(current_templates_path).mkdir(parents=True, exist_ok=True)
    Path(new_templates_path).mkdir(parents=True, exist_ok=True)

    # Load the command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filepath", type=str, help="Input template filepath. Defaults to all files in the current_templates folder.")
    parser.add_argument("-o", "--output", type=str, help="Output template filepath. Defaults to all files in the new_templates folder.")
    parser.add_argument("-n", "--normaliser", type=str, help="Upper or lowercase normaliser. Set to uppercase or lowercase.")
    parser.add_argument("-d", "--dynamic", help="Convert mappings to dynamic templates.", default=False, action="store_true")
    parser.add_argument("-c", "--compression", help="Enable best compression.", default=False, action="store_true")
    parser.add_argument("-r", "--refresh", help="Set the refresh interval seconds.", type=int)
    args = parser.parse_args()

    if not len(sys.argv) > 1:
        print("Error, No arguments provided. Try dynamic-template-generator.py --help")
        sys.exit(1)

    # Write the output file to the same directory and in input file specified in args.filepath.
    if args.output and args.output == "." and not args.filepath:
        print("Error, Specify and input file when writing the output file to the same directory.")
        sys.exit(1)

    if args.output and args.output == "." and args.filepath.lower().startswith(current_templates_path.lower()):
        print("Error, Can't write new template to the current_templates folder. This will overwrite the input template file.")
        sys.exit(1)

    # Validate the case normaliser.
    if args.normaliser and args.normaliser.lower().strip() not in ["uppercase", "lowercase"]:
        print("Error, Normaliser only accepts uppercase or lowercase, not {0}.".format(str(args.normaliser)))
        sys.exit(1)

    # Lowercase the case normaliser.
    if args.normaliser:
        args.normaliser = args.normaliser.lower().strip()

    main(args)