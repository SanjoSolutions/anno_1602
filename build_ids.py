import re


def parse(file_path):
    constants = dict()
    data = dict()
    object = data
    objects = []
    attribute_names = []
    at_attribute_values = dict()

    def convert_string_to_value(string: str, attribute_name = None):
        if attribute_name is not None:
            plus_number_regexp = re.compile(r'^\+(\d+)$')
            match = plus_number_regexp.match(string)
            if match:
                attribute_name = attribute_name
                attribute_name_without_at = attribute_name[1:] if attribute_name[0] == '@' else attribute_name
                if attribute_name_without_at in constants:
                    base_value = constants[attribute_name_without_at]
                elif attribute_name[0] == '@' and attribute_name in at_attribute_values:
                    base_value = at_attribute_values[attribute_name]
                else:
                    base_value = objects[-1][-2][attribute_name_without_at]
                number = int(match.group(1))
                base_value_type = type(base_value)
                if base_value_type is int:
                    return base_value + number
                elif base_value_type is tuple:
                    return (base_value[0], base_value[1] + number)
                else:
                    return (base_value, number)

        float_regexp = re.compile(r'^[+-]?\d+\.\d+$')
        match = float_regexp.match(string)
        if match:
            return float(string)

        int_regexp = re.compile(r'^[+-]?\d+$')
        match = int_regexp.match(string)
        if match:
            return int(string)

        tuple_regexp = re.compile(r'^.+(?:, ?.+)+$')
        match = tuple_regexp.match(string)
        if match:
            return tuple(convert_string_to_value(value) for value in re.split(', ?', match.group(0)))

        number_plus_number_regexp = re.compile(r'^(\d+)\+(\d+)$')
        match = number_plus_number_regexp.match(string)
        if match:
            number_a = int(match.group(1))
            number_b = int(match.group(2))
            value = number_a + number_b
            return value

        constant_plus_number_regexp = re.compile(r'^(.+)\+(\d+)$')
        match = constant_plus_number_regexp.match(string)
        if match:
            constant_name = match.group(1)
            number = int(match.group(2))
            constant = constants[constant_name]
            value = constant + number
            return value

        if string in constants:
            return constants[string]
        else:
            return string

    with open(file_path, mode='r', encoding='utf-8') as file:
        line_regexp = re.compile(r'^([^\t ]+)\s*([=:])\s*([^\t ][^\t]*)$')
        line = file.readline()
        while line:
            stripped_line = line.strip()
            if stripped_line.startswith(';---'):
                print(stripped_line)
            line = remove_comment(line)
            line = line.strip()
            if line == 'EndObj;':
                if 'Nummer' in object or '@Nummer' in object:
                    object = objects.pop()
                object = objects.pop()
                attribute_names.pop()
            else:
                match = line_regexp.match(line)
                if match:
                    operand_a = match.group(1)
                    operator = match.group(2)
                    operand_b = match.group(3)
                    if operator == '=':
                        constants[operand_a] = convert_string_to_value(operand_b, operand_a)
                    elif operator == ':':
                        if operand_a == 'Objekt':
                            object[operand_b] = dict()
                            objects.append(object)
                            attribute_names.append(operand_b)
                            object = object[operand_b]
                        else:
                            value = convert_string_to_value(operand_b, operand_a)

                            if operand_a in {'Nummer', '@Nummer'}:
                                if type(objects[-1]) is not list:
                                    array = list()
                                    objects[-1][attribute_names[-1]] = array
                                    objects.append(array)
                                object = dict()
                                objects[-1].append(object)

                            if operand_a in object:
                                if type(object[operand_a]) is not list:
                                    object[operand_a] = [object[operand_a]]
                                object[operand_a].append(value)
                            else:
                                object[operand_a] = value

                            if operand_a[0] == '@':
                                at_attribute_values[operand_a] = value

                            if operand_a in {'Nummer', '@Nummer'}:
                                print(value)

            line = file.readline()

    return data


def remove_comment(line: str):
    if line[0] == ';':
        return ''
    else:
        try:
            index = line.index(' ;')
            return line[:index]
        except ValueError:
            return line


if __name__ == '__main__':
    parse('../haeuser.txt')
