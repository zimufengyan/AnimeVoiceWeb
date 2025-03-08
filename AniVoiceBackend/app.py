import json
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    current_user
)
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import logging
import redis
import os
import glob
import uuid

from settings import DevelopmentConfig
from utils import *
# from database import PostgresDB, UserTable
from database_v2 import db, UserManager, AudioRecordManager
from form import *

log_path = "./runtime.log"
max_log_size = 10
configure_root_logger(logging.DEBUG)

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
CORS(app, resources={r'/*': {'origins': '*'}}, supports_credentials=True)
jwt = JWTManager(app)
redis_client = redis.StrictRedis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DB'], decode_responses=True)
mail = Mail(app)
bcrypt = Bcrypt(app)
db.init_app(app)
user_manager = UserManager(app)
audio_record_manager = AudioRecordManager(app)
migrate = Migrate(app, db)
with app.app_context():
    db.create_all()
    db.session.commit()

# db = PostgresDB(dbname=app.config['DATABASE_NAME'], user=app.config['DATABASE_USER'], password=app.config['DATABASE_PD'])
# db.connect()

# 创建用户表对象
# user_manager = UserTable(db, table_name=app.config['USERTABLE_NAME'])

# 读取角色-模型数据
character_info_path = "./character_info.json"
with open(character_info_path, 'r', encoding='utf-8') as f:
    character_dic = json.loads(f.read())
    logging.info("successfuy load character_info.json")

current_activated_character = None  # 当前激活的角色

addr = f"http://{app.config['HOST']}:{app.config['PORT']}"


@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@jwt.user_identity_loader
def user_identity_lookup(user):
    logging.info('user_identity_lookup', user)
    return str(user.id)


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    logging.info('user identity:', identity)
    return user_manager.get_user_by_id(int(identity))

# @app.route('/gen_audios/<path:filename>')
# def serve_audio(filename):
#     return send_from_directory('gen_audios', filename)  # 确保路径正确


@app.route('/login', methods=['POST'])
def login():
    logging.info('post for login')
    form = request.get_json()
    email = form.get('email')
    password = form.get('password')
    salt = form.get("salt")
    user = user_manager.get_user_by_email(email)
    if user:
        logging.info(f"login user email: {email}, found user: {user.name}")
        if bcrypt.check_password_hash(user.pwd, password):
             # 生成 JWT Token
            access_token = create_access_token(identity=user)       # 已经写了user_identity_lookup， 直接传入UserInfo对象
            avatar_path = os.path.join(app.config['UPLOAD_ICONS_LOCAL_DIR'], user.pic)
            avatar_url = f"{addr}/{avatar_path}"  # 使用完整 URL 返回头像地址
            response = LoginResponseForm(code='1', username=user.name, avatar=avatar_url, index=user.id, rate=user.rate, token=access_token, message="登陆成功")
            return jsonify(response.to_dict()), 200
        else:
            logging.info("密码错误")
            response = LoginResponseForm(code='2', message="密码错误")      # 密码错误
            return jsonify(response.to_dict()), 200
    else:
        logging.info(f"login user email: {email}, not found user!")
        response = LoginResponseForm(code='3', message="该用户不存在, 请注册")      # 用户不存在
        return jsonify(response.to_dict()), 200


@app.route('/get_recent_audio_records', methods=['GET'])
@jwt_required()
def get_recent_audio_records():
    logging.info(f'current user: {current_user}')
    return jsonify({"code": 1, "message": "获取成功"}), 200
    

@app.route('/generate_voice', methods=["GET"])
@jwt_required()
def generate_voice():
    current_user = get_jwt_identity()
    logging.info(f"current user: {current_user}")

    belong = request.args.get('belong')
    character = request.args.get('character')
    text = request.args.get('text')
    text_split = request.args.get('split', 0)
    lang = request.args.get("lang", 'zh')

    if belong not in character_dic:
        logging.warning(f"belong {belong} not in character_dic")
        return jsonify({"code" : "-1", "messaage": "该IP不存在"}), 201
    all_characters: dict = character_dic[belong]
    if character not in all_characters:
        logging.warning(f"character {character} not in all_characters")
        return jsonify({"code": "-2", "message": "该角色不存在或暂不支持"}), 201
    
    model_info = all_characters[character]
    # texts = [text] if not text_split else text.split('/n')

    global current_activated_character

    if not current_activated_character or character != current_activated_character:
        # 角色改变，重新设置模型
        # prepare SOVITS backend
        logging.info(f"set model for character: {character}")
        succ1, _ = execute_request(url=app.config["SOVITS_SET_GPT_API"], 
                        param={'weights_path': model_info['gpt_weights_path']})
        succ2, _ = execute_request(url=app.config["SOVITS_SET_VIT_API"], 
                        param={'weights_path': model_info['sovits_weights_path']})
        if not succ1 or not succ2:
            return jsonify({"code" : "-1", "messaage": "无法连接GPT-SoVITS"}), 500
        logging.info(f"successfully set model for character: {character}")
        current_activated_character = character
        
    # TODO: TTS 
    with open(model_info['prompt_text_path'], 'r', encoding='utf-8') as f:
        prompt_text = f.read().replace('/n', '').strip()

    form = TTSReqForm(
        text = text, text_lang=lang, ref_audio_path=model_info['ref_audio_path'],
        prompt_lang=model_info['promot_lang'], prompt_text=prompt_text
    )
    succ, response = execute_request(app.config["SOVITS_TTS_API"], 
                                     param=form.to_dict())
    if not succ:
        return jsonify({"code" : "-1", "messaage": "无法连接GPT-SoVITS"}), 500
    logging.info('successfully generate voice')
    unique_id = str(uuid.uuid4())
    audio_path = os.path.join(app.config["GENERATED_AUDIO_DIR"], unique_id + '.wav')
    audio_local_path = os.path.join(app.config["GENERATED_AUDIO_LOCAL_DIR"], unique_id + '.wav')
    with open(audio_path, "wb") as f:
            f.write(response.content)
    logging.info(f"successfully write audio into path : {audio_path}")
    local_audio_url = f"{addr}/{audio_local_path}"
    return jsonify({"code": 1, "audio_url": local_audio_url, "message": "语音生成成功"}), 200


@app.route('/get_salt', methods=['GET'])
def get_salt():
    # 获取该用户的盐值，用于前端login生成相同的加密串
    email = request.args.get('email')
    user = user_manager.get_user_by_email(email)
    if user:
        logging.info(f"用户盐值: {user.salt}")
        return jsonify({"code": "1", "salt": user.salt, "message": "查找成功"}), 200
    else:
        logging.info("该用户不存在")
        return jsonify({"code": "-1", "salt": "", "message": "该用户不存在"}), 200


@app.route('/register', methods=['POST'])
def register():
    form = request.get_json()
    email = form.get('email')
    username = form.get('username')
    password = form.get('password')
    validation_code = form.get('validationCode')
    salt = form.get("salt")
    key_perfix = app.config['CODE_REDIS_KEY_PERFIX']
    salt_length = app.config['SALT_LENGTH']
    hashed_password = bcrypt.generate_password_hash(password, salt_length).decode('utf-8')
    logging.info(f"hashed password: {hashed_password}")

    # 获取存储在 Redis 中的验证码
    redis_key = f"{key_perfix}{email}"
    stored_code = redis_client.get(redis_key)
    if not stored_code:
        logging.info('验证码已过期或未发送')
        return jsonify(LoginResponseForm(code='3', message='验证码已过期或未发送').to_dict()), 400
    if stored_code != validation_code:
        logging.info('验证码不正确')
        return jsonify(LoginResponseForm(code='3', message='验证码不正确').to_dict()), 400

    user = user_manager.get_user_by_email(email)
    if user:
        logging.info(f"email ({email}) had benn registered")
        return jsonify(LoginResponseForm(code='4', message='该用户已存在').to_dict()), 400

    num_users = user_manager.count_all_users()
    rate = generate_rate()
    avator = get_random_image(app.config['DEFAULT_ICON_DIR'])
    avator_name = os.path.basename(avator)
    item = UserItem(name=username, sex='0', age=18, pic=avator_name, pwd=hashed_password, phone='', email=email, rate=rate, index=num_users+1, salt=salt)
    user_id, success = user_manager.insert_user(item)
    # user_id, success = None , False
    if success:
        avatar_path = os.path.join(app.config['UPLOAD_ICONS_LOCAL_DIR'], avator)
        avatar_url = f"{addr}/{avatar_path}"  # 使用完整 URL 返回头像地址
        response = LoginResponseForm(code='1', username=username, avatar=avatar_url, index=str(user_id), rate=rate, message="注册成功")
    else:
        response = LoginResponseForm(code='2', message="注册失败")
    return jsonify(response.to_dict()), 200


# 登出接口（可选，仅作前端清理状态）
@app.route('/logout', methods=['POST'])
def logout():
    # Flask-JWT-Extended 不支持 token 失效化，前端仅需清理 token
    return jsonify({"message": "登出成功"}), 200


@app.route('/get_email_code', methods=['GET'])
def get_email_code():
    logging.info('post for getting email code')
    email = request.args.get('email')

    # 验证邮箱格式
    if not validate_email(email):
        return jsonify({'code': -1, 'message': '邮箱格式不正确'}), 400

    # 生成 6 位随机验证码
    verification_code = ''.join(random.choices('0123456789', k=6))
    timeout = app.config['CODE_TIMEOUT']

    # 构造邮件内容
    subject = "验证码"
    body = f"您好, 您正在注册本网站，您的验证码是：{verification_code}，请在 {timeout // 60} 分钟内使用。"

    try:
        # 发送邮件
        msg = Message(subject, recipients=[email], body=body, sender=app.config['MAIL_USERNAME'])
        mail.send(msg)
        logging.info("send email code successfully")

         # 将验证码存储到 Redis，有效期 timeout // 60 分钟
        key_perfix = app.config['CODE_REDIS_KEY_PERFIX']
        redis_key = f"{key_perfix}{email}"  # 使用邮箱作为 key
        redis_client.setex(redis_key, timeout, verification_code)  

        return jsonify({'code': 1, 'message': '验证码发送成功'}), 200
    except Exception as e:
        logging.info("send email code failed")
        return jsonify({'code': -1, 'message': f'发送邮件失败: {str(e)}'}), 500
    

@app.route("/get_belong_statics", methods=['GET'])
def get_belong_statics():
    """获取当前IP所属的所有角色的静态资源"""
    belong = request.args.get('belong')     # 立绘所属IP
    if belong not in character_dic:
        # 不支持的IP
        logging.info(f"not supperted ip: {belong}")
        return jsonify({'code': -1, "urls": []}), 501

    stands_dir = app.config['STANDS_DIR']
    stands_local_dir = app.config['STANDS_LOCAL_DIR']
    stand_extension = app.config['STAND_EXT']
    chracter_avator_dir = app.config['CHARACTER_AVATOR_DIR']
    chracter_avator_local_dir = app.config['CHARACTER_AVATOR_LOCAL_DIR']
    avator_extension = app.config['CHARACTER_AVATOR_EXT']
    logging.info(f'start capturing stands and avators from {os.path.join(stands_dir, belong)} and {os.path.join(chracter_avator_dir, belong)}, respectively')

    avators = glob.glob(os.path.join(chracter_avator_dir, belong, f'*.{avator_extension}')) 
    # avators = glob.glob(chracter_avator_dir + '/' + belong + f'/*.{avator_extension}') 
    stands = glob.glob(os.path.join(stands_dir, belong, f'*.{stand_extension}')) 

    stands.sort()
    avators.sort()

    logging.info(f"capture {len(stands)} stands and {len(avators)} avators")
 
    if len(stands) != len(avators):
        logging.info(f"length of stands ({len(stands)}) != length of avators ({len(avators)})")
        return jsonify({'code': -1, "urls": []}), 501   
    names, stand_urls, avator_urls = [], [], []
    for stand, avator in zip(stands, avators):
        names.append(os.path.splitext(os.path.basename(stand))[0])
        stand_urls.append(f"{addr}/{os.path.join(stands_local_dir, belong, os.path.basename(stand))}")
        avator_urls.append(f"{addr}/{os.path.join(chracter_avator_local_dir, belong,  os.path.basename(avator))}")
    return jsonify({'code': 1, "names": names, "stands": stand_urls, "avators": avator_urls}), 200
    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)