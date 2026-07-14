import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'vetmax_cok_gizli_anahtar_123'

# Dosya Yükleme Ayarları
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static/images/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Veritabanı Bağlantısı
db_path = os.path.join(os.path.dirname(__file__), 'vetmax.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ----------------- VERİTABANI MODELLERİ -----------------

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), default='fa-stethoscope')
    image = db.Column(db.String(120), nullable=True)


# YENİ: Tedaviler Tablosu
class Treatment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), default='fa-kit-medical')
    image = db.Column(db.String(120), nullable=True)


# ----------------- KULLANICI ROTALARI -----------------

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/hakkimizda')
def about():
    return render_template('about.html')


@app.route('/hizmetlerimiz')
def services():
    all_services = Service.query.all()
    return render_template('services.html', services=all_services)


# YENİ: Tedaviler Kullanıcı Sayfası
@app.route('/tedavilerimiz')
def treatments():
    all_treatments = Treatment.query.all()
    return render_template('treatments.html', treatments=all_treatments)


@app.route('/iletisim')
def contact():
    return render_template('contact.html')


# ----------------- ADMIN PANELİ ROTALARI -----------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Başarıyla giriş yaptınız.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Hatalı kullanıcı adı veya şifre!', 'danger')

    return render_template('admin/login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    all_services = Service.query.all()
    all_treatments = Treatment.query.all()  # YENİ: Tedavileri Çek
    return render_template('admin/dashboard.html', services=all_services, treatments=all_treatments)


# Admin: Hizmet Ekleme
@app.route('/admin/service/add', methods=['POST'])
def add_service():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    title = request.form.get('title')
    description = request.form.get('description')
    icon = request.form.get('icon', 'fa-stethoscope')

    file = request.files.get('image')
    image_filename = None
    if file and file.filename != '' and allowed_file(file.filename):
        image_filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    if title and description:
        new_service = Service(title=title, description=description, icon=icon, image=image_filename)
        db.session.add(new_service)
        db.session.commit()
        flash('Hizmet başarıyla eklendi!', 'success')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/service/delete/<int:id>')
def delete_service(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    service_to_delete = Service.query.get_or_404(id)
    if service_to_delete.image:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], service_to_delete.image))
        except:
            pass
    db.session.delete(service_to_delete)
    db.session.commit()
    flash('Hizmet silindi.', 'info')
    return redirect(url_for('admin_dashboard'))


# YENİ: Admin Tedavi Ekleme
@app.route('/admin/treatment/add', methods=['POST'])
def add_treatment():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    title = request.form.get('title')
    description = request.form.get('description')
    icon = request.form.get('icon', 'fa-kit-medical')

    file = request.files.get('image')
    image_filename = None
    if file and file.filename != '' and allowed_file(file.filename):
        image_filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    if title and description:
        new_treatment = Treatment(title=title, description=description, icon=icon, image=image_filename)
        db.session.add(new_treatment)
        db.session.commit()
        flash('Tedavi başarıyla eklendi!', 'success')

    return redirect(url_for('admin_dashboard'))


# YENİ: Admin Tedavi Silme
@app.route('/admin/treatment/delete/<int:id>')
def delete_treatment(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    treatment_to_delete = Treatment.query.get_or_404(id)
    if treatment_to_delete.image:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], treatment_to_delete.image))
        except:
            pass
    db.session.delete(treatment_to_delete)
    db.session.commit()
    flash('Tedavi silindi.', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))


def init_db():
    with app.app_context():
        db.create_all()
        # Admin oluşturma
        if not Admin.query.filter_by(username='admin').first():
            hashed_pw = generate_password_hash('vetmax123')
            default_admin = Admin(username='admin', password_hash=hashed_pw)
            db.session.add(default_admin)
            db.session.commit()

        # Hizmetler boşsa doldur
        if Service.query.count() == 0:
            default_services = [
                Service(title="Klinik Hizmetleri",
                        description="Uzman hekim kadromuz eşliğinde gerçekleştirilen periyodik sağlık taramaları, check-up ve aşı programları...",
                        icon="fa-stethoscope"),
                Service(title="Kuaför Hizmetleri",
                        description="Dostlarımızın tüy ve deri sağlığını korumak amacıyla hijyenik pet kuaför ünitemizde...",
                        icon="fa-scissors"),
                Service(title="Pet İstasyon",
                        description="Seyahatlerinizde ya da yoğun iş günlerinizde gözünüzün arkada kalmaması için kedi dostlarımıza...",
                        icon="fa-house-chimney-window"),
                Service(title="Evlere Mama Servisi",
                        description="Dostlarımızın gelişim evrelerine ve kronik sağlık durumlarına en uygun mamaları ulaştırıyoruz...",
                        icon="fa-bone"),
                Service(title="Pet Ozon Terapi",
                        description="Kronik deri hastalıkları, alerjiler ve operasyon sonrası iyileşme süreçlerinde hücre yenilenmesini destekler...",
                        icon="fa-kit-medical"),
                Service(title="Yoğun Bakım",
                        description="Kritik durumdaki, ağır travma veya ameliyat geçirmiş hastalarımızı kesintisiz gözetim altında tutuyoruz...",
                        icon="fa-syringe"),
                Service(title="Dermatoloji",
                        description="Geçmeyen kaşıntılar, mantar, egzama, tüy dökülmesinde mikroskobik muayeneler ve alerji testleriyle...",
                        icon="fa-heart"),
                Service(title="Göz Hastalıkları",
                        description="Katarakt, glokom, kornea ülserleri ve göz yaşı kanalı tıkanıklıkları gibi durumlarda mikro-cerrahi...",
                        icon="fa-eye"),
                Service(title="İç Hastalıkları",
                        description="Kalp, böbrek, karaciğer ve endokrin sistem bozukluklarında derinlemesine teşhis ve tedavi...",
                        icon="fa-prescription-bottle-medical")
            ]
            db.session.bulk_save_objects(default_services)
            db.session.commit()

        # YENİ: Tedaviler boşsa doldur
        if Treatment.query.count() == 0:
            default_treatments = [
                Treatment(title="Kısırlaştırma Operasyonları",
                          description="Erkek ve dişi kedi-köpek dostlarımız için gaz anestezisi ve estetik dikiş teknikleri kullanılarak yapılan konforlu cerrahi operasyonlardır.",
                          icon="fa-cat"),
                Treatment(title="Ortopedik Cerrahi & Kırık Tedavisi",
                          description="Kaza, düşme ve travma kaynaklı kırıklar, çıkıklar ve çapraz bağ yırtıklarında titanyum plak ve pin sistemleriyle modern cerrahi müdahale sunuyoruz.",
                          icon="fa-bone"),
                Treatment(title="Diş Sağlığı & Tartar Temizliği",
                          description="Ultrasonik cihazlarımızla (scaler) diş taşı temizliği, parlatma ve diş eti hastalıklarının medikal tedavilerini gerçekleştiriyoruz.",
                          icon="fa-tooth"),
                Treatment(title="Kritik Enfeksiyon Tedavileri",
                          description="Gençlik hastalığı (Distemper), Kanlı İshal (Parvovirüs) ve FIP gibi hayati risk taşıyan ağır viral enfeksiyonların yoğun bakım destekli kombine tedavileri.",
                          icon="fa-shield-dog"),
                Treatment(title="Onkolojik Cerrahi & Kemoterapi",
                          description="Tümör teşhisi, biyopsi süreçleri, cerrahi uzaklaştırma operasyonları ve hastanın konforunu artıracak bireyselleştirilmiş kemoterapi protokolleri.",
                          icon="fa-ribbon"),
                Treatment(title="Göz Cerrahi Operasyonları",
                          description="Cherry eye (üçüncü göz kapağı sarkması), entropiyon-ektropiyon (göz kapağı anomalileri) cerrahisi ve kornea dikim operasyonları.",
                          icon="fa-eye")
            ]
            db.session.bulk_save_objects(default_treatments)
            db.session.commit()


if __name__ == '__main__':
    init_db()
    app.run(debug=True)