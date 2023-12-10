import io
import logging
import os
import sys
import uuid

from flask import render_template, request, send_file
from werkzeug.utils import secure_filename

from config.config import g_allowed_extensions, g_tmp_path, logger
from src.app import App
from src.log.CapturingLogger import CapturingLogger


@App.instance.flask.route("/")
def home():
    return render_template("home.html")


@App.instance.flask.route("/api/cumulative-expense-reports", methods=["POST"])
def api_process_cumulative_expense_report():
    if 'file' not in request.files:
        return "", 400

    file = request.files['file']

    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in g_allowed_extensions

    if file.filename == '' or file.content_type != 'application/pdf' or not allowed_file(file.filename):
        return "", 400

    original_source_filename = secure_filename(file.filename)
    real_source_filename = uuid.uuid4()
    file.save(os.path.join(g_tmp_path, real_source_filename.__str__()))

    def run():
        report = App.instance.cumulative_expense_report_processor.process_report(
            file_name=original_source_filename,
            real_path=os.path.realpath(os.path.join(g_tmp_path, real_source_filename.__str__()))
        )

        return App.instance.cumulative_expense_report_excel_generator.generate(report)

    output_file_id, logs = CapturingLogger.capture_html_logs(run)

    return {
        "id": output_file_id.__str__(),
        "logs": logs
    }, 200


@App.instance.flask.route("/api/cumulative-expense-reports/<uuid:report_id>", methods=["GET"])
def api_retrieve_cumulative_expense_report(report_id: uuid.UUID):
    path = os.path.join(g_tmp_path, report_id.__str__() + ".xlsx")

    if not os.path.exists(path):
        return "", 404

    response = send_file(
        path,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=False
    )
    return response
