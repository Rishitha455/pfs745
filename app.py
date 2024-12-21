from flask import Flask,request,render_template,redirect,url_for,flash,session,send_file
import mysql.connector
#from mysql.connector import(connection)
from otp import genotp
from cmail import sendmail
from stoken import encode,decode
from flask_session import Session
from io import BytesIO
import flask_excel as excel
import re
app=Flask(__name__)
excel.init_excel(app)
app.config['SESSION_TYPE']='filesystem'
app.secret_key="ab123"
mydb=mysql.connector.connect(host='localhost',user='root',password='Admin',db='snmproject')
#mydb=connection.MySQLConnection(user='root',password='Admin',host='localhost',database='snmproject')
Session(app)
@app.route('/')
def home():
    return render_template('welcome.html')
@app.route('/create',methods=['GET','POST'])
def create():
    if session.get('user'):
        if request.method=='POST':
            print(request.form)
            username=request.form['username']
            email=request.form['email']
            password=request.form['password']
            confirmpassword=request.form['cpassword']
            cursor=mydb.cursor()
            cursor.execute('select count(user_email) from users where user_email=%s',[email])
            result=cursor.fetchone()
            print(result)
            if result[0]==0:
                gotp=genotp()
                udata={'username':username,'useremail':email,'password':password,'otp':gotp}
                print(gotp)
                subject='OTP for Simple Notes Manager'
                body=f'otp for registration of simple notes manager {gotp}'
                sendmail(to=email,subject=subject,body=body)
                flash('OTP has sent to given mail')
                return redirect(url_for('otp',enudata=encode(data=udata)))
            elif result[0]>0:
                flash('Email already existed')
                return redirect(url_for('login'))
            else:
                return 'something went wrong'
        return render_template('create.html')
@app.route('/otp/<enudata>',methods=['GET','POST'])
def otp(enudata):
    if request.method=='POST':
        uotp=request.form['OTP']
        try:
            dudata=decode(data=enudata)
        except exception as e:
            print(e)
            return 'something went wrong'
        else:
            if dudata['otp']==uotp:
                cursor=mydb.cursor()
                cursor.execute('insert into users(user_name,user_email,password) values(%s,%s,%s)',[dudata['username'],dudata['useremail'],dudata['password']])
                mydb.commit()
                cursor.close()
                flash('Successfully Registered ')
                return redirect(url_for('login'))
            else:
               return 'otp was wrong please register again'
    return render_template('otp.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if not session.get('user'):
        if request.method=='POST':
            uemail=request.form['email']
            pwd=request.form['password']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(user_email) from users where user_email=%s',[uemail])
            bdata=cursor.fetchone()  #(1,) or (0,)
            if bdata[0]==1:
                 cursor.execute('select password from users where user_email=%s',[uemail])
                 bpassword=cursor.fetchone()  #(0x31373034000000000000,)
                 if pwd==bpassword[0].decode('utf-8'):
                    session['user']=uemail
                    print(session)
                    return redirect(url_for('dashboard'))
                 else:
                    flash('password was wrong')
                    return redirect(url_for('login'))
            elif bdata[0]==0:
                flash('Email not existed')
                return redirect(url_for('create'))
            else:
                return 'something went wrong'
        return render_template('login.html')
    else:
        return redirect(url_for('dashboard'))
    
@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))
@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from users where user_email=%s',[session.get('user')])
            user_id=cursor.fetchone()
            if user_id:
                try:
                    cursor.execute('insert into notes(title,n_description,user_id) values(%s,%s,%s)',[title,description,user_id[0]])
                    mydb.commit()
                    cursor.close()
                except mysql.connector.errors.IntegrityError:
                    print(e)
                    flash('Duplicate Title Entry')
                    return redirect(url_for('dashboard'))
                        
                except mysql.connector.errors.ProgrammingError:
                    flash('could not add notes')
                    print(mysql.connector.errors.ProgrammingError)
                    return redirect(url_for('dashboard'))
                else:
                        flash('notes added successfully')
                        return redirect(url_for('dashboard'))
            else:
                return 'something is wrong'
        return render_template('addnotes.html')
    else:
        return redirect(url_for('login'))
        
@app.route('/viewallnotes',methods=['GET','POST'])
def viewallnotes():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from users where user_email=%s',[session.get('user')])
            user_id=cursor.fetchone()
            cursor.execute('select n_id,title,create_at from notes where user_id=%s',[user_id[0]])
            ndata=cursor.fetchall()
        except Exception as e:
            print(e)
            flash('No data found')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewallnotes.html',ndata=ndata)
    else:
        return redirect(url_for('login'))
@app.route('/viewnotes/<n_id>')
def viewnotes(n_id):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select * from notes where n_id=%s',[n_id])
            ndata=cursor.fetchone()
        except Exception as e:
            print(e)
            flash('No data found')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewnotes.html',ndata=ndata)
    else:
        return redirect(url_for('login'))
@app.route('/updatenotes/<n_id>',methods=['GET','POST'])
def updatenotes(n_id):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from notes where n_id=%s',[n_id])
        ndata=cursor.fetchone()
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update notes set title=%s,n_description=%s where n_id=%s',[title,description,n_id])
            mydb.commit()
            cursor.close()
            flash('notes updated successfully')
            return redirect(url_for('viewnotes',n_id=n_id))
        return render_template('updatenotes.html',ndata=ndata)
    else:
        return redirect(url_for('login'))
@app.route('/deletenotes/<n_id>')
def deletenotes(n_id):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('delete from notes where n_id=%s',[n_id])
            mydb.commit()
            cursor.close()
        except Exception as e:
                print(e)
                flash('could not delete notes')
                return redirect(url_for('viewallnotes'))
        else:
                flash('Notes deleted successfully')
                return redirect(url_for('viewallnotes'))
    else:
        return redirect(url_for('login'))
@app.route('/uploadfile',methods=['GET','POST'])
def uploadfile():
    if session.get('user'):
        if request.method=='POST':
            filedata=request.files['file']
            fname=filedata.filename
            fdata=filedata.read()
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select user_id from users where user_email=%s',[session.get('user')])
                user_id=cursor.fetchone()
                cursor.execute('insert into filedata(filename,fdata,added_by) values(%s,%s,%s)',[fname,fdata,user_id[0]])
                mydb.commit()
            except Exception as e:
                print(e)
                flash('could not upload file')
                return redirect(url_for('dashboard'))
            else:
                flash('File uploaded successfully')
                return redirect(url_for('dashboard'))
        return render_template('uploadfile.html')
    else:
        return redirect(url_for('login'))
@app.route('/allfiles')
def allfiles():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from users where user_email=%s',[session.get('user')])
            user_id=cursor.fetchone()
            cursor.execute('select fid,filename,created_at from filedata where added_by=%s',[user_id[0]])
            filesdata=cursor.fetchall()
        except Exception as e:
            print(e)
            flash('No data found')
            return redirect(url_for('dashboard'))
        else:
            return render_template('allfiles.html',filesdata=filesdata)
    else:
        return redirect(url_for('login'))
@app.route('/viewfile/<fid>')
def viewfile():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select filename,fdata from filedata where fid=%s',[fid])
            fdata=cursor.fetchone()
            bytes_data=BytesIO(fdata[1])
            return send_file(bytes_data,download_name=fdata[0],as_attachment=False)
        except Exception as e:
            print(e)
            flash('could not open file')
            return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))
@app.route('/downloadfile/<fid>')
def downloadfile(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select filename,fdata from filedata where fid=%s',[fid])
            fdata=cursor.fetchone()
            bytes_data=BytesIO(fdata[1])
            return send_file(bytes_data,download_name=fdata[0],as_attachment=True)
        except Exception as e:
            print(e)
            flash('could not download file')
            return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))
@app.route('/deletefile/<fid>')
def deletefile(fid):
    if session.get('user'):
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('delete from filedata where fid=%s',[fid])
                mydb.commit()
                cursor.close()
            except Exception as e:
                print(e)
                flash('could not delete the file')
                return redirect(url_for('viewallfiles'))
            else:
                flash('file deleted successfully')
                return redirect(url_for('viewallfiles'))
    else:
        return redirect(url_for('login'))
@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from users where user_email=%s',[session.get('user')])
            user_id=cursor.fetchone() #(1,)
            cursor.execute('select n_id,title,create_at from notes where user_id=%s',[user_id[0]])
            ndata=cursor.fetchall()   #[(1,'python','2024-12-16 11:14:25',),(2,'mysql','2024-12-16 11:14:53',)]
        except Exception as e:
            print(e)
            flash('No data found')
            return redirect(url_for('dashboard'))
        else:
            array_data=[list(i) for i in ndata]
            columns=['Notesid','Title','Content','Created_time']
            array_data.insert(0,columns)
            #[['Notesid','Title','Content','Created_time'],[1,'python','2024-12-16 11:14:25'],[2,'mysql','2024-12-16 11:14:53']]
            return excel.make_response_from_array(array_data,'xlsx',filename='notesdata')
    else:
        return redirect(url_for('login'))
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))
@app.route('/search',methods=['GET','POST'])
def search():
    if session.get('user'):
        try:
            if request.method=='POST':
                sdata=request.form['sname']
                strg=['A-Za-z0-9']
                pattern=re.compile(f'^{strg}',re.IGNORECASE)
                if (pattern.match(sdata)):
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('select * from notes where n_id like %s or title like %s or n_description like %s or create_at like %s',[sdata+'%',sdata+'%',sdata+'%',sdata+'%'])
                    sdata=cursor.fetchall()
                    cursor.close()
                    return render_template('dashboard.html',sdata=sdata)
                else:
                    flash('No Data Found')
                    return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash("can't find anything")
            return redirect(url_for('dashboard'))
        
    else:
        return redirect(url_for('login'))
app.run(use_reloader=True,debug=True)