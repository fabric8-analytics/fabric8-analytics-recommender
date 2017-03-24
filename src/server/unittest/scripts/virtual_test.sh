#! /bin/bash
clear
#HOMEPATH=`pwd`/../../../
#cd "$HOMEPATH"
echo "8***********************"
echo `pwd` 
virtualenv --system-site-packages env
. env/bin/activate
pip install -r deployment/requirements.txt
PYTHONPATH=`pwd` py.test server/unittest/
/bin/echo -e "\e[1;31mTYPE deactivate TO EXIT VIRTUAL ENVIRONMENT\e[0m"
