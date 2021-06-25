from aiohttp import web
import jinja2
from pathlib import Path
from dbconn import db_block,db_block1
from cryptography.fernet import InvalidToken
from cryptography.fernet import Fernet
import psycopg2
from urllib.parse import urlencode

secret_key = Fernet.generate_key()
fernet = Fernet(secret_key)

home_path = Path(__file__).parent
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(home_path)))

x=[]
y=[]

with db_block1() as db:
    db.execute('''
    select no,sn from student;
    ''')
    items = tuple([tuple(row) for row in db])
passwords=dict((y, x) for x, y in items)   ######密码是序号



with db_block() as db:
    db.execute('''
    select sn,Staff_no from course;
    ''')
    passwords2=list(db)
for item in passwords2:
    x.append(item.staff_no)
    y.append(item.sn)
passwords2={x[n]: y[n] for n in range(len(x))}
passwords3= {"manger": "123456"}

###学生
async def login_form_page(request):
    template = jinja_env.get_template('login.html')
    return web.Response(text=template.render(),
                        content_type="text/html")
#####教师
async def login_form_page2(request):
    template = jinja_env.get_template('login2.html')
    return web.Response(text=template.render(),
                        content_type="text/html")

#####管理人员
async def login_form_page3(request):
    template = jinja_env.get_template('login3.html')
    return web.Response(text=template.render(),
                        content_type="text/html")




###学生
async def handle_login(request):
    parmas = await request.post()  # 获取POST请求的表单字段数据
    global username
    username = parmas.get("username")
    password = parmas.get("password")

    if passwords.get(username) != password:  # 比较密码
        return web.HTTPFound('/login')  # 比对失败重新登录
    resp = web.HTTPFound('/student')
    set_secure_cookie(resp, "session_id", username)

    return resp

#####教师
async def handle_login2(request):
    parmas = await request.post()  # 获取POST请求的表单字段数据
    global username2
    username2 = parmas.get("username")
    password = parmas.get("password")
    # print("username2:",username2,type(username2))
    # print("password:",password,type(password))
    # print("passwords2.get(username2):",passwords2.get(username2),type(passwords2.get(username2)))
    if passwords2.get(username2) != password:  # 比较密码
        return web.HTTPFound('/login2')  # 比对失败重新登录
    resp = web.HTTPFound('/teacher')
    set_secure_cookie(resp, "session_id", username2)
    return resp

#####管理人员
async def handle_login3(request):
    parmas = await request.post()  # 获取POST请求的表单字段数据
    username = parmas.get("username")
    password = parmas.get("password")
    if passwords3.get(username) != password:  # 比较密码
        return web.HTTPFound('/login3')  # 比对失败重新登录
    resp = web.HTTPFound('/manger')
    set_secure_cookie(resp, "session_id", username)
    return resp


async def handle_logout(request):
    resp = web.HTTPFound('/login')
    resp.del_cookie("session_id")
    return resp 

def get_current_user(request):
    user_id = get_secure_cookie(request, "session_id")
    return user_id


def get_secure_cookie(request, name):
    value = request.cookies.get(name)
    if value is None:
        return None
    try:
        buffer = value.encode('utf-8')  # 将文本转换成字节串
        buffer = fernet.decrypt(buffer)
        secured_value = buffer.decode('utf-8')  # 将加密的字节串转换成文本
        return secured_value
    except InvalidToken:
        print("Cannot decrypt cookie value")
        return None

def set_secure_cookie(response, name, value, **kwargs):
    value = fernet.encrypt(value.encode('utf-8')).decode('utf-8')
    response.set_cookie(name, value, **kwargs)

async def home_page(request):
    template = jinja_env.get_template('index.html')
    return web.Response(text=template.render(),
                        content_type="text/html")
###学生
async def student(request):
    with db_block1() as db:
        db.execute('''
        select student.name,stu_sn,student.clss,course.name,time,place
        from course_grade,student,course
        where stu_sn=student.sn
        and cou_sn=course.no
        and stu_sn=%(sn)s ;
        ''',dict(sn=username))
        items2 = [row for row in db]
    template = jinja_env.get_template('list.html')
    return web.Response(text=template.render(items2=items2),
                        content_type="text/html")

#####教师
async def teacher(request):
    with db_block1() as db:
        db.execute('''
        select name,data,time,place
        from course
        where Staff_no=%(Staff_no)s ;
        ''',dict(Staff_no=username2))
        items4 = [row for row in db]
    template = jinja_env.get_template('teacher.html')
    return web.Response(text=template.render(items4=items4),
                        content_type="text/html")
####管理者
async def manger(request):
    template = jinja_env.get_template('manger.html')
    return web.Response(text=template.render(),
                        content_type="text/html")


######学生
async def check_semester(request):
    datas =await request.post() 
    data = datas.get("semester")
    with db_block1() as db:
        db.execute("""
        select course.name,course.data,grade
        from course_grade,student,course
        where stu_sn=student.sn
        and cou_sn=course.no
        and stu_sn=%(sn)s 
        and data=%(data)s ;
        """,dict(sn=username,data=data))
        items3 = [row for row in db]
        template = jinja_env.get_template('list2.html')
    return web.Response(text=template.render(items3=items3),
                           content_type="text/html")



#####教师
async def check_schedule(request):
    datas =await request.post() 
    data = datas.get("semester")
    with db_block() as db:
        db.execute("""
        select name,data,place
        from course
        where Staff_no=%(Staff_no)s 
        and data=%(data)s;
        """,dict(Staff_no=username2,data=data))
        items5 = list(db)
        template = jinja_env.get_template('teacher2.html')
    return web.Response(text=template.render(items5=items5),
                           content_type="text/html")

###教师
async def check_kecheng(request):
    datas =await request.post() 
    data = datas.get("semester")
    with db_block() as db:
        db.execute("""
        select student.name,stu_sn,grade,cou_sn
        from course,course_grade,student
        where Staff_no=%(Staff_no)s 
        and stu_sn=student.sn
        and course.name=%(data)s;
        """,dict(Staff_no=username2,data=data))
        items50 =list(db)
        template = jinja_env.get_template('teacher3.html')
    return web.Response(text=template.render(items50=items50),
                           content_type="text/html")
#######教师
async def view_grade_action(request):
    stu_sn = request.match_info.get("stu_sn")
    cou_sn = request.match_info.get("cou_sn")
    if stu_sn is None or cou_sn is None:
        return web.HTTPBadRequest(text="stu_sn, cou_sn, must be required")

    with db_block() as db:
        db.execute("""
        SELECT grade FROM course_grade
            WHERE stu_sn = %(stu_sn)s AND cou_sn = %(cou_sn)s;
        """, dict(stu_sn=stu_sn, cou_sn=cou_sn))
        record = db.fetch_first()
    if record is None:
        return web.HTTPNotFound(text=f"no such grade: stu_sn={stu_sn}, cou_sn={cou_sn}")
    webpage = jinja_env.get_template('edit.html').render(stu_sn=stu_sn,
                                                         cou_sn=cou_sn,
                                                         grade=record.grade)
    return web.Response(text=webpage, content_type="text/html")

#####教师
async def edit_grade_action(request):
    stu_sn = request.match_info.get("stu_sn")
    cou_sn = request.match_info.get("cou_sn")

    if stu_sn is None or cou_sn is None:
        return web.HTTPBadRequest(text="stu_sn, cou_sn, must be required")

    params = await request.post()
    grade = params.get("grade")

    with db_block() as db:
        db.execute("""
        UPDATE course_grade SET grade=%(grade)s
        WHERE stu_sn = %(stu_sn)s AND cou_sn = %(cou_sn)s
        """, dict(stu_sn=stu_sn, cou_sn=cou_sn, grade=grade))
        
    return web.HTTPFound(location="/teacher")


#####教师
def grade_deletion_dialog(request):
    stu_sn = request.match_info.get("stu_sn")
    cou_sn = request.match_info.get("cou_sn")
    if stu_sn is None or cou_sn is None:
        return web.HTTPBadRequest(text="stu_sn, cou_sn, must be required")

    with db_block() as db:
        db.execute("""
        select stu_sn,grade,cou_sn,student.name as stu_name,course.name as cou_name
        from course,course_grade,student
        where stu_sn=%(stu_sn)s 
        and stu_sn=student.sn
        and cou_sn=%(cou_sn)s;
        """, dict(stu_sn=stu_sn, cou_sn=cou_sn))

        record = db.fetch_first()
    if record is None:
        return web.HTTPNotFound(text=f"no such grade: stu_sn={stu_sn}, cou_sn={cou_sn}")

    webpage = jinja_env.get_template('grade_dialog_deletion.html').render(record=record)
    return web.Response(text=webpage, content_type="text/html")


####教师
def delete_grade_action(request):
    stu_sn = request.match_info.get("stu_sn")
    cou_sn = request.match_info.get("cou_sn")
    if stu_sn is None or cou_sn is None:
        return web.HTTPBadRequest(text="stu_sn, cou_sn, must be required")

    with db_block() as db:
        db.execute("""
        DELETE FROM course_grade
            WHERE stu_sn = %(stu_sn)s AND cou_sn = %(cou_sn)s
        """, dict(stu_sn=stu_sn, cou_sn=cou_sn))

    return web.HTTPFound(location="/teacher")

####教师
async def action_grade_add(request):
    params = await request.post()
    stu_sn = params.get("stu_sn")
    cou_sn = params.get("cou_sn")
    grade = params.get("grade")

    if stu_sn is None or cou_sn is None or grade is None:
        return web.HTTPBadRequest(text="stu_sn, cou_sn, grade must be required")
    grade=int(grade)
    try:
        with db_block() as db:
            db.execute("""
            INSERT INTO course_grade (stu_sn, cou_sn, grade) 
            VALUES ( %(stu_sn)s, %(cou_sn)s, %(grade)s)
            """, dict(stu_sn=stu_sn, cou_sn=cou_sn, grade=grade))
    except psycopg2.errors.UniqueViolation:

        return web.HTTPNotFound(text=f"已有学号为{stu_sn}的学生的{cou_sn}课程的成绩")
    except psycopg2.errors.ForeignKeyViolation as ex:
        return web.HTTPBadRequest(text=f"无此学生或课程: {ex}")
    return web.HTTPFound(location="/teacher")
####管理者
async def plan(request):
    with db_block1() as db:
        db.execute("""
        select distinct clss,course.name, course.data,time,place
        from student,course,course_grade
        where cou_sn=course.no
        and stu_sn=student.sn;
        """,)
        items6 = [row for row in db]
        template = jinja_env.get_template('manger2.html')
    return web.Response(text=template.render(items6=items6),
                           content_type="text/html")
###管理者
async def check_plan(request):
    datas =await request.post() 
    data = datas.get("semester")
    with db_block1() as db:
        db.execute("""
        select distinct clss,course.name, course.data from student,course,course_grade
        where cou_sn=course.no
        and stu_sn=student.sn
        and clss=%(clss)s;
        """,dict(clss=data))
        items7 = [row for row in db]
        template = jinja_env.get_template('manger3.html')
    return web.Response(text=template.render(items7=items7),
                           content_type="text/html")
                           
###管理者
async def class_pf(request):
    with db_block1() as db:
        db.execute("""
        select clss,student.name,course.name,grade
        from course,student,course_grade
        where cou_sn=course.no
        and stu_sn=student.sn
        """,)
        items8 = [row for row in db]
        template = jinja_env.get_template('manger4.html')
    return web.Response(text=template.render(items8=items8),
                           content_type="text/html")


####管理者
async def check_results(request):
    datas =await request.post() 
    data = datas.get("semester")
    with db_block1() as db:
        db.execute("""
        select clss,student.name,course.name,grade
        from course,student,course_grade
        where cou_sn=course.no
        and stu_sn=student.sn
        and clss=%(clss)s;
        """,dict(clss=data))


        items9 = [row for row in db]
        template = jinja_env.get_template('manger5.html')
    return web.Response(text=template.render(items9=items9),
                           content_type="text/html")
                
app = web.Application()
app.add_routes([
    web.get('/',home_page),
    web.get('/student',student),
    web.get('/teacher',teacher),
    web.get('/manger',manger),   
    web.get('/login', login_form_page),
    web.get('/login2', login_form_page2),
    web.get('/login3', login_form_page3),
    web.get('/plan', plan),
    web.get('/class_pf', class_pf),
    web.get('/teacher/kecheng/edit/{stu_sn}/{cou_sn}', view_grade_action),
    web.get('/grade/delete/{stu_sn}/{cou_sn}', grade_deletion_dialog),
    web.post('/student/semester', check_semester),
    web.post('/teacher/schedule', check_schedule),
    web.post('/teacher/kecheng', check_kecheng),
    web.post('/action/grade/add', action_grade_add),
    web.post('/action/kecheng/edit/{stu_sn}/{cou_sn}',edit_grade_action),
    web.get('/action/grade/delete/{stu_sn}/{cou_sn}', delete_grade_action),
    web.post('/manger/plan',check_plan),
    web.post('/manger/results',check_results),
    web.post('/loginn', handle_login),
    web.post('/login2', handle_login2),
    web.post('/login3', handle_login3),
    web.post('/logout', handle_logout),
    web.static("/", home_path / "static"),
    ])

if __name__ == "__main__":
    web.run_app(app, port=8080)
