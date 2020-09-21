import deathbycaptcha

 # Put your DBC account username and password here.
username = "username"
password = "password"
# you can use authtoken instead of user/password combination
# activate and get the authtoken from DBC users panel
authtoken = ""
captcha_file = 'test.jpg'  # image

# client = deathbycaptcha.SocketClient(username, password, authtoken)
#to use http client
client = deathbycaptcha.HttpClient(username, password, authtoken)


try:
    balance = client.get_balance()
    print(balance)

    # Put your CAPTCHA file name or file-like object, and optional
    # solving timeout (in seconds) here:
    captcha = client.decode(captcha_file, type=2)
    if captcha:
        # The CAPTCHA was solved; captcha["captcha"] item holds its
        # numeric ID, and captcha["text"] item its list of "coordinates".
        print ("CAPTCHA %s solved: %s" % (captcha["captcha"], captcha["text"]))

        if '':  # check if the CAPTCHA was incorrectly solved
            client.report(captcha["captcha"])
except deathbycaptcha.AccessDeniedException:
    # Access to DBC API denied, check your credentials and/or balance
    print ("error: Access to DBC API denied, check your credentials and/or balance")
