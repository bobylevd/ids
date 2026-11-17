#!/bin/bash
# Usage: check-masking.sh <file-or-dir>...
# Prints each line that holds an email, a phone number or a credential. Exit 0 = clean.
EMAIL='[A-Za-z0-9._+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'
PHONE='\+[0-9][0-9 ()-]{8,}[0-9]'
AWS_KEY='A[KS]IA[0-9A-Z]{16}'
PRIVATE_KEY='BEGIN [A-Z ]*PRIVATE KEY'
JWT='eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}'
ASSIGNED='(password|passwd|secret|api[_-]?key|authorization)["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"']?[^[:space:]"'"'"'<|]{8,}'
grep -rEnIi -e "$EMAIL" -e "$PHONE" -e "$AWS_KEY" -e "$PRIVATE_KEY" -e "$JWT" -e "$ASSIGNED" "$@"
[ $? -eq 1 ]
