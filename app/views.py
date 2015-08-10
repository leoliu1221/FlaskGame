from flask import Flask, render_template,redirect,url_for,request,session,flash
from functools import wraps
from flask.ext.socketio import SocketIO,emit
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
from app import app, socketio
import random

#mimic the function in django on get_or_create. 
#input session, model and kwargs. 
def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.iteritems())
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        session.commit()
        return instance, True

#reset the money for all players
@app.route('/reset')
def reset_money():
    from app import db,models
    startMoney=200
    print '*'*80
    print 'in reset_money def, generating the initial banks. '
    for b in db.session.query(models.Bank).all():
        b.money = startMoney
        print 'process',b
    session.commit()
    print 'reset finished. '
    return redirect(url_for('chat'))    



#login required decorator
def login_required(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('you need to login first.')
            print 'redirecting to login'
            return redirect(url_for('login'))
    return wrap

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/colors')
@login_required
def colors():
    return render_template('colors.html')

@app.route('/chat')
@login_required
def chat():
    from app import db,models
    print '*'*80
    print 'in chat def, generating the initial banks. '
    userBank, status = get_or_create(db.session,models.Bank,role=session['role'],username=session['username'])
    print userBank
    return render_template('chat.html',money = userBank.money)

#this is for generating the false csv list of results. 
def get_rand_no_duplicate(sList,number=10):
    print '*'*80
    print 'in get_rand_no_duplicate'
    print len(sList)
    resultList = []
    i=0
    while i<number:
        iTemp = random.randrange(0,len(sList))
        print iTemp
        if iTemp not in resultList:
            resultList.append(iTemp)
            i+=1
    return [sList[i] for i in resultList]


@app.route('/login',methods=['GET','POST'])
def login():
    
    error = None
    if request.method == 'POST':
        if request.form['username']!='admin' or request.form['password']!='admin':
            error = 'Invalid credentials'
        else:
            session['logged_in']=True
            session['username']=request.form['username']
            session['password']=request.form['password']
            session['role']=request.form['role']
            flash('you were just logged in!')

            if session['role']!='judge':
                return redirect(url_for('colors'))
            else:
                with open('app/results.csv','r') as f:
                    content = f.read()
                fakeResultList = get_rand_no_duplicate(content.split(',\r'),10)
                session['results'] = '<br>'.join(fakeResultList)
                return redirect(url_for('chat'))
                #return render_template('chat.html',results = '<br>'.join(fakeResultList))
            #return render_template('colors.html',session=session )
    return render_template('login.html',error = error)

@app.route('/logout')
def logout():
    #reset money if judge log out. 
    session.pop('logged_in',None)
    session.pop('username',None) 
    session.pop('password',None)
    flash('you were just logged out!')
    return redirect(url_for('login'))
def ack():
    print 'message was received'


@socketio.on('connect')
def test_connect():
    emit('new_message', {'data': 'Connected', 'count': 0})
    print 'connected'


#There are only 4 types of messages 
#tester1 -> judge      t1
#tester2 -> judge      t2
#judge -> tester1      j1
#judge -> tester2      j2
#connect message. 
@socketio.on('connect_message')
def connected(msg):
    print 'in connnect_message'
    emit('connect_message',{'data':msg['data'],'role':msg['role'],'time':str(datetime.now())[10:19]})
#usr_money is handled here
@socketio.on('money_message')
def transfer_money(msg):
    from app import db,models
    print '*'*80
    print 'in transfer_money'
    if session['role']=='judge':
        try:
            print session['role'],'to',msg['toRole'] 
            print 'money: ',msg['data']
    try:
        #current bank of the judge
        judge_current= db.session.query(Bank).filter_by(role='judge')
        print judge_current

        if session['role'] !='judge':
            #Trans row
            trans = models.Trans(fromRole, toRole, amount)

        pass
    except Exception,err:
        print err



@socketio.on('winnter_message')
@login_required
def winnter(msg):
    #if a winner is declared, return each player and judge to result page. 
    return redirect(url_for('result',messages = msg))


@app.route('/result')
@login_required
def result():
    msg = request.args['messages']
    print 'in result', 'msg is:',msg
    return msg


#usr_message is handle here. 
@socketio.on('usr_message')
def send_message(msg):
    from app import db,models
    try:
        if session['role']!='judge':
            tempM = models.Message(session['role'],msg['data'],'judge')
        else:
            tempM = models.Message(session['role'],msg['data'],msg['toRole'])
    except KeyError:
        return redirect(url_for('login'))
    db.session.add(tempM)
    db.session.commit()

    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('new_message',{'data':msg['data'],'count':session['receive_count'],'role':session['role'],'time':str(datetime.now())[10:19],'toRole':msg['toRole']},callback=ack,broadcast=True)


if __name__=='__main__':
    #app.run(debug=True)i
    socketio.run(app,host='0.0.0.0')
