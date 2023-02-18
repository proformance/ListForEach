import copy
import json
import re

MACRO_NAME = 'ListForEach'

def process_template(template: dict, templateParameterValues: dict) -> tuple:
    new_template = copy.deepcopy(template)
    
    if not transform_template_section(template, new_template, templateParameterValues, 'Resources'):
        return 'failed', template
    if not transform_template_section(template, new_template, templateParameterValues, 'Outputs'):
        return 'failed', template
    return 'success', new_template

def transform_template_section(template: dict, new_template: dict, templateParameterValues: dict, section: str) -> bool:
    for name, resource in template[section].items():
        if MACRO_NAME in resource:
            # Get the number of times to multiply the resource
            commaSeparatedList = new_template[section][name].pop(MACRO_NAME)
            # Remove the original resource from the template but take a local copy of it
            resourceToMultiply = new_template[section].pop(name)
            # Create a new block of the resource multiplied with names ending in the iterator and the placeholders substituted
            resourcesAfterMultiplication = multiply(name, resourceToMultiply, commaSeparatedList, templateParameterValues)
            if not set(resourcesAfterMultiplication.keys()) & set(new_template[section].keys()):
                new_template[section].update(resourcesAfterMultiplication)
            else:
                return False
    return True

def update_placeholder(resource_structure, iteration, listValues):
    resourceString = json.dumps(resource_structure)
    indexPlaceHolderCount = resourceString.count('%d') + resourceString.count('%s')

    if indexPlaceHolderCount == 0:
        print("No occurences of placeholder found in JSON, therefore nothing will be replaced")
        return resource_structure
    
    # Placeholders exists
    print("Found {} occurrences of placeholder in JSON, replacing with iterator value {}".format(indexPlaceHolderCount, iteration))

    regex = r"(\%d|\%s)"
    matches = re.findall(regex, resourceString, re.MULTILINE)
    placeHolderReplacementValues = [iteration if m == '%d' else listValues[iteration] for m in matches]
    #Replace the decimal placeholders using the list - the syntax below expands the list
    resourceString = resourceString % (*placeHolderReplacementValues,)
    return json.loads(resourceString)


def multiply(resource_name, resource_structure, listValues, templateParameterValues):
    resources = {}
    #Loop according to the number of times we want to multiply, creating a new resource each time
    if isinstance(listValues, dict) and 'Ref' in listValues:
        listValues = templateParameterValues[listValues['Ref']]
        count = len(listValues)
    else:
        count = listValues
    for iteration in range(count):
        print("Multiplying '{}', iteration count {}".format(resource_name,iteration))        
        multipliedResourceStructure = update_placeholder(resource_structure, iteration, listValues)
        resources[resource_name+str(iteration)] = multipliedResourceStructure
    return resources


def handler(event, context):
    result = process_template(event['fragment'], event['templateParameterValues'])
    return {
        'requestId': event['requestId'],
        'status': result[0],
        'fragment': result[1],
    }
