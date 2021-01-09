echo "START AVO UI"
#Explore model
docker run -i -t  \
    -P \
    -p 8761:8050\
    --mount type=bind,source="$PWD"/app,target=/app \
    --rm ui sh -c 'cd /app/ && python app.py;'
echo "Exited with status $?"
    #-p 80:80\
