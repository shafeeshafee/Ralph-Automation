import smtplib

server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('cloudega.alertmanager@gmail.com', 'karbzitrmafcdlai')
server.sendmail('cloudega.alertmanager@gmail.com', 'cgordon.dev@gmail.com', 'Test email from Python')
server.quit()