from datetime import datetime, timedelta, timezone
from pathlib import Path
from fpdf import FPDF
from pikepdf import Pdf, Page, Rectangle
from carrier_viberbot.settings import MEDIA_ROOT
from threading import Thread

from customer.models import Subscriber
from order.models import WaybillEntry


def szs(n):
    n = str(n)
    if len(n) == 1:
        return "0" + n
    return n


def render_pdf_template(vid=None, number=None, id_client=None, time=None, date=None, surname=None, name=None,
                        patronymic=None, ser_doc=None, num_doc=None, kod_org_doc=None, tr_mark=None,
                        tr_reg_num=None, odometer_value=None):

    months = ("января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября",
              "декабря")

    full_name = surname + " " + name + " " + patronymic
    fio_driver = surname + " " + name[:1] + "." + patronymic[:1] + "."

    day = szs(date.split(".")[0])
    month = szs(date.split(".")[1])
    year = szs(date.split(".")[2])

    hours = szs(time.split("-")[0])
    minutes = szs(time.split("-")[1])
    dep_time = hours + "-" + minutes

    array = ((str(number), 295, 43),
             ("от " + day + "/" + month + "/" + year + "г.", 142, 67),
             (day + "/" + month + "/" + year + "г.", 237, 176),
             (day + "." + month + "." + year + "г.", 253, 284),
             ("«" + day + "» " + (months[int(month) - 1]) + " " + year + "г.", 42, 510),
             (hours + " - " + minutes, 319, 176),
             (hours + " : " + minutes, 328, 284),
             (hours + " час " + minutes + " мин ", 42, 502),
             (tr_mark, 127, 118),
             (str(id_client), 310, 128),
             (tr_reg_num, 127, 128),
             (full_name, 85, 136),
             (ser_doc + " " + num_doc, 102, 154),
             (kod_org_doc, 263, 154),
             (str(odometer_value), 310, 202),
             (fio_driver, 265, 277),
             (dep_time, 146, 332))

    media_files = paths_files(vid)
    thread = Thread(target=set_text_in_template_pdf, args=[array, media_files[4], media_files[2]])
    thread.daemon = True
    thread.start()
    return media_files


def new_pdf(path_to_pdf=''):
    pdf = Pdf.new()
    pdf.save(path_to_pdf)


def paths_files(vid):
    # offset = timedelta(hours=int(Subscriber.objects.get(user=vid).time_zone))
    offset = timedelta(hours=int(WaybillEntry.objects.get(applicant=Subscriber.objects.get(user=vid)).time_zone))
    tz = timezone(offset, name='TZ')
    now = datetime.now(tz=tz)
    date_time = now.strftime("%d.%m.%Y_%H-%M")
    path_to_media = Path(MEDIA_ROOT)
    if not Path.exists(path_to_media):
        Path.mkdir(path_to_media)
    v = str(vid)
    user_dir_name = str(v).replace("/", "").replace("+", "").replace("=", "")
    user_path = path_to_media.joinpath(user_dir_name)
    if not Path.exists(user_path):
        Path.mkdir(user_path)
    filename_pdf = Path("Waybill_" + str(date_time) + ".pdf")
    # filename_pdf = Path("Путевой лист.pdf")
    attached_data_filename = Path("data.pdf")
    attached_data = user_path.joinpath(attached_data_filename)
    pdf_media_file = user_path.joinpath(filename_pdf)
    if not Path(attached_data).exists():
        t = Thread(target=new_pdf, args=[attached_data])
        t.setDaemon(True)
        t.start()

    return user_path, user_dir_name, pdf_media_file, filename_pdf, attached_data
    # return user_path, user_dir_name, pdf_media_file, filename_pdf, attached_data, str(date_time)


def set_text_in_template_pdf(text_data, path_to_pdf_attached_data, path_output_pdf):
    path_to_pdf_template = Path(MEDIA_ROOT).joinpath("template.pdf")
    path_to_ttf = Path(MEDIA_ROOT).joinpath("dejavu-sans-condensed_997.ttf")

    pdf = FPDF(orientation='L', unit='pt', format='A4')
    pdf.add_page()
    pdf.add_font('DejaVu', '', path_to_ttf, uni=True)
    pdf.set_font('DejaVu', '', 7)
    for i in text_data:
        pdf.set_font_size(7)
        pdf.set_xy(i[1], i[2])
        pdf.cell(7, 7, i[0])

    pdf.output(path_to_pdf_attached_data)

    pdf1 = Pdf.open(path_to_pdf_template)
    pdf2 = Pdf.open(path_to_pdf_attached_data)
    page1 = Page(pdf1.pages[0])
    page2 = Page(pdf2.pages[0])
    page1.add_overlay(page2, Rectangle(0, 0, 842, 595))
    pdf1.save(path_output_pdf)
