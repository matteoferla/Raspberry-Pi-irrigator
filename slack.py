import requests, unicodedata, os, re

def slack(msg):
    """
    Send message to a slack webhook.
    Copy pasted code from Michelanglo. Obvs nothing malicious is sent from here!
    :param msg:
    :return:
    """
    print(msg)
    # sanitise.
    if 'SLACK_WEBHOOK' not in os.environ:
        return False
    msg = unicodedata.normalize('NFKD',msg).encode('ascii','ignore').decode('ascii')
    msg = re.sub('[^\w\s\-.,;?!@#()\[\]]','', msg)
    r = requests.post(url=os.environ['SLACK_WEBHOOK'],
                      headers={'Content-type': 'application/json'},
                      data=f"{{'text': '{msg}'}}")
    if r.status_code == 200 and r.content == b'ok':
        return True
    else:
        print(f'{msg} failed to send (code: {r.status_code}, {r.content}).')
        return False