import pywhatkit
pywhatkit.start_server()
def sendWAmsg(dataframe):
    try:
        pywhatkit.sendwhatmsg("+919545166688", f"Hello Python + {dataframe}",22,13)
        print("WA Msg successfully sent")
    except Exception as e:
        print(f"ERROR :: Failed to send WA msg as {str(e)}")

dataframe = ["Test ", "the ","stock ",'List']
sendWAmsg(dataframe)