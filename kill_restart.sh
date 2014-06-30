#kill
echo "killing supervisord and gunicord instances..."
sudo pkill supervisord
sudo pkill gunicorn
echo "starting supervisord"
sudo supervisord -c simple.conf
echo "Done... list pf supervisord and gunicorn:"
ps aux |grep "supervisord\|gunicorn" |grep -v grepx
