import xml.etree.ElementTree as ET

def get_bug_data(xml_path):
    bugs = []
    tree = ET.parse(xml_path)
    root = tree.getroot()
    for element in root.findall(".//table"):
        bug_id = element[1].text
        summary = element[2].text
        description = element[3].text
        fixing_commit = element[7].text
        fixing_commit_time = element[8].text
        fixed_files = element[9].text
        
        bug_data = {"bug_id": bug_id,
                    "summary": summary,
                    "description": description,
                    "fixing_commit": fixing_commit,
                    "fixing_commit_time": fixing_commit_time,
                    "fixed_files": fixed_files}
        bugs.append(bug_data)

    bugs = sorted(bugs, key=lambda d: d['fixing_commit_time'])

    length = len(bugs)
    starting_index = length - int(length*0.4)
    latest_bugs = bugs[starting_index:length]
    
    return latest_bugs

def main():
    xml_path = '../dataset/birt.xml'
    latest_bugs = get_bug_data(xml_path)
    for bug in latest_bugs:
        print(bug['bug_id'])#,str(bug['summary'] or ''), str(bug['description'] or ''))


if __name__ == "__main__":
    main()