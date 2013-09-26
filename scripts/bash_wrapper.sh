#!/bin/bash
# образец bash-обертки над питоновским кодом
cat > ${bamboo.build.working.directory}/python_file.py <<EOF
#-----------PYTHON-START--------------
""" python code here """
EOF

/usr/bin/env python python_file.py || exit 253

rm ${bamboo.build.working.directory}/python_file.py