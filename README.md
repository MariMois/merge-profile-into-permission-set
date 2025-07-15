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
```bash
pip install -r requirements.txt
