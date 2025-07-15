# Merge Profile Into Permission Set

A Python utility to merge Salesforce **Profile** metadata into a **Permission Set** XML, producing a deployable Permission Set.

## ✨ Features
✅ Merges all compatible permissions from a Profile into a Permission Set  
✅ Deduplicates entries  
✅ Cleans namespaces for a valid deployable file  
✅ **NEW:** When a permission exists in both, the script merges them and picks the **less restrictive** option (e.g. `editable=true` if either side has it)  
✅ Logs what was added, updated, or skipped  

---

## 📦 Requirements
- Python 3.9+ (comes with `xml.etree.ElementTree` built in)

Install additional dependencies (none currently):

MyProfile.profile-meta.xml
MyPermSet.permissionset-meta.xml
merge_profile_into_pset.py


2. Run the script:

python merge_profile_into_pset.py
After running, you will get:

    ✅ Merged.permissionset-meta.xml – the merged and deployable Permission Set.

    📄 merge_log.txt – a detailed log of what was added, updated, or skipped.

## ⚖️ Conflict Resolution

When a permission element exists in both the Profile and the Permission Set, the script merges them field by field:

    Boolean fields (readable, editable, etc.):
    If either side is true, the merged result will be true (less restrictive).

    Non‑boolean fields:
    The value from the Permission Set is kept.

This ensures the merged Permission Set is as permissive as possible without losing any existing configurations.

## 📂 Example Log Output

🔧 Merging MyProfile.profile-meta.xml (Profile) into MyPermSet.permissionset-meta.xml (PermissionSet)
✅ MERGE <fieldPermissions>: added 5, updated 3 (less restrictive)
✅ MERGE <userPermissions>: added 2, updated 0 (less restrictive)
♻️ MERGE <label>: replaced with profile value
✅ Merged file written to Merged.permissionset-meta.xml


