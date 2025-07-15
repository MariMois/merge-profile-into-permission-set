import os
import sys
import xml.etree.ElementTree as ET
from copy import deepcopy

# ---------- CONFIG ----------
VALID_SECTIONS = {
    "applicationVisibilities",
    "classAccesses",
    "customMetadataTypeAccesses",
    "customPermissions",
    "customSettingAccesses",
    "description",
    "fieldPermissions",
    "flowAccesses",
    "hasActivationRequired",
    "label",
    "license",
    "objectPermissions",
    "pageAccesses",
    "recordTypeVisibilities",
    "ServicePresenceStatusAccesses",
    "tabSettings",
    "userLicense",
    "userPermissions"
}

KEY_FIELDS = {
    'userPermissions': 'name',
    'fieldPermissions': 'field',
    'objectPermissions': 'object',
    'recordTypeVisibilities': 'recordType',
    'applicationVisibilities': 'application',
    'classAccesses': 'apexClass',
    'pageAccesses': 'apexPage',
    'tabSettings': 'tab',
    'customPermissions': 'name',
    'customMetadataTypeAccesses': 'name',
    'customSettingAccesses': 'name',
    'ServicePresenceStatusAccesses': 'servicePresenceStatus'
}

# ---------- HELPERS ----------
def strip_ns(tag: str) -> str:
    return tag.split('}', 1)[1] if '}' in tag else tag

def remove_namespaces(elem):
    elem.tag = strip_ns(elem.tag)
    for child in elem:
        remove_namespaces(child)

def detect_files():
    xml_files = [f for f in os.listdir('.') if f.lower().endswith('.xml')]
    profiles = []
    psets = []
    for f in xml_files:
        try:
            tree = ET.parse(f)
            root = strip_ns(tree.getroot().tag)
            if root == 'Profile':
                profiles.append(f)
            elif root == 'PermissionSet':
                psets.append(f)
        except ET.ParseError:
            continue
    return profiles, psets

def elem_key(elem):
    tag = strip_ns(elem.tag)
    kfield = KEY_FIELDS.get(tag)
    if not kfield:
        return None
    for child in elem:
        if strip_ns(child.tag) == kfield:
            return (tag, child.text.strip() if child.text else '')
    return None

def index_elements(elements):
    result = {}
    for e in elements:
        k = elem_key(e)
        if k:
            result[k] = e
    return result

def merge_dicts_less_restrictive(dict1, dict2):
    merged = dict(dict2)  # start with PermissionSet values
    for k, v in dict1.items():
        if k in merged:
            # if both are bool-like
            v1 = str(v).strip().lower()
            v2 = str(merged[k]).strip().lower()
            if v1 in ('true','false') and v2 in ('true','false'):
                merged[k] = 'true' if (v1 == 'true' or v2 == 'true') else 'false'
            # else: keep the PermissionSet's value (less destructive)
        else:
            merged[k] = v
    return merged

def elem_to_dict(elem):
    d = {}
    for child in elem:
        tag = strip_ns(child.tag)
        d[tag] = child.text.strip() if child.text else ''
    return d

def dict_to_elem(tag, data):
    el = ET.Element(tag)
    for k, v in data.items():
        c = ET.Element(k)
        c.text = str(v)
        el.append(c)
    return el

# ---------- MAIN MERGE ----------
def merge(profile_file, pset_file):
    log = []
    log.append(f"🔧 Merging {profile_file} (Profile) into {pset_file} (PermissionSet)\n")

    ptree = ET.parse(profile_file)
    proot = ptree.getroot()

    stree = ET.parse(pset_file)
    sroot = stree.getroot()

    # Build section maps
    prof_sections = {}
    for child in proot:
        tag = strip_ns(child.tag)
        prof_sections.setdefault(tag, []).append(child)

    ps_sections = {}
    for child in sroot:
        tag = strip_ns(child.tag)
        ps_sections.setdefault(tag, []).append(child)

    # Merge logic
    for section, elems in prof_sections.items():
        if section not in VALID_SECTIONS:
            log.append(f"⏩ SKIP section <{section}> (not valid in PermissionSet)\n")
            continue

        # Repeatable keyed sections
        if section in KEY_FIELDS:
            existing = index_elements(ps_sections.get(section, []))
            updated = 0
            added = 0
            for elem in elems:
                k = elem_key(elem)
                if k:
                    if k not in existing:
                        sroot.append(deepcopy(elem))
                        added += 1
                    else:
                        # Merge field-by-field
                        p_dict = elem_to_dict(elem)
                        s_dict = elem_to_dict(existing[k])
                        merged_dict = merge_dicts_less_restrictive(p_dict, s_dict)
                        # Replace existing element
                        new_elem = dict_to_elem(section, merged_dict)
                        # remove old
                        parent_index = list(sroot).index(existing[k])
                        sroot.remove(existing[k])
                        sroot.insert(parent_index, new_elem)
                        existing[k] = new_elem
                        updated += 1
            log.append(f"✅ MERGE <{section}>: added {added}, updated {updated} (less restrictive)\n")

        else:
            # Single-occurrence section
            if section not in ps_sections:
                sroot.append(deepcopy(elems[0]))
                log.append(f"✅ MERGE <{section}>: added from profile\n")
            else:
                # merge single text content: less restrictive only for known bools? (just override)
                # for now, override if different
                existing_text = "".join((c.text or "").strip() for c in ps_sections[section][0])
                profile_text = "".join((c.text or "").strip() for c in elems[0])
                if existing_text != profile_text:
                    # replace
                    sroot.remove(ps_sections[section][0])
                    sroot.append(deepcopy(elems[0]))
                    log.append(f"♻️ MERGE <{section}>: replaced with profile value\n")
                else:
                    log.append(f"ℹ️ SKIP <{section}>: identical already present\n")

    # Clean namespaces in output
    remove_namespaces(sroot)

    # Write merged permission set
    ET.indent(stree, space="  ")
    output_file = "Merged.permissionset-meta.xml"
    stree.write(output_file, encoding="utf-8", xml_declaration=True)
    log.append(f"\n✅ Merged file written to {output_file}\n")

    # Write log
    with open("merge_log.txt", "w", encoding="utf-8") as f:
        f.writelines(log)

    print("".join(log))

# ---------- ENTRY ----------
if __name__ == "__main__":
    profiles, psets = detect_files()
    if len(profiles) != 1 or len(psets) != 1:
        print("❌ Please place exactly ONE Profile and ONE Permission Set XML in this folder.")
        sys.exit(1)

    merge(profiles[0], psets[0])
