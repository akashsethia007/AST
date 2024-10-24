import pywhatkit
#pywhatkit.start_server()
def sendWAmsg(dataframe):
    try:
        phlist = ["+919545166688", "+919123390240", "+918197324666"]
        for num in phlist:
            pywhatkit.sendwhatmsg_instantly(f"{num}", dataframe,10,True,3)
        print("WA Msg successfully sent")
    except Exception as e:
        print(f"ERROR :: Failed to send WA msg as {str(e)}")
