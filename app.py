from flask import Flask, render_template, request, jsonify
import subprocess
import re
import time
import platform
import ipaddress

app = Flask(__name__)


def validate_target(target):
    """Validate hostname or IP address."""
    if not target or not isinstance(target, str):
        return False, "يرجى إدخال عنوان صحيح"

    target = target.strip()

    if len(target) > 253:
        return False, "العنوان طويل جداً"

    # Check for shell injection characters
    if re.search(r'[;&|<>$`\\!()]', target):

        return False, "عنوان غير صالح - يحتوي على رموز ممنوعة"

    # Validate as IP address
    try:
        ipaddress.ip_address(target)
        return True, target
    except ValueError:
        pass

    # Validate as hostname
    hostname_pattern = r'^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(\.[A-Za-z0-9-]{1,63})*\.?$'
    if re.match(hostname_pattern, target):
        return True, target

    return False, "عنوان غير صالح"


def get_ping_command(target, count=4):
    """Build ping command based on OS."""
    system = platform.system().lower()

    if system == "windows":
        return ["ping", "-n", str(count), target]
    else:
        return ["ping", "-c", str(count), "-W", "2", target]


def parse_ping_output(output):
    """Parse ping output to extract statistics."""
    stats = {
        "transmitted": 0,
        "received": 0,
        "loss_percent": 0,
        "min_time": None,
        "avg_time": None,
        "max_time": None,
        "times": []
    }

    lines = output.split('')

    for line in lines:
        # Extract individual ping times
        time_match = re.search(r'time[<=]([\d.]+)\s*ms', line)
        if time_match:
            stats["times"].append(float(time_match.group(1)))

        # Extract packet stats
        packet_match = re.search(r'(\d+) packets transmitted,\s*(\d+) received', line)
        if packet_match:
            stats["transmitted"] = int(packet_match.group(1))
            stats["received"] = int(packet_match.group(2))

        # Extract loss percentage
        loss_match = re.search(r'(\d+)% packet loss', line)
        if loss_match:
            stats["loss_percent"] = int(loss_match.group(1))

        # Extract RTT stats
        rtt_match = re.search(r'min/avg/max.*?=\s*([\d.]+)/([\d.]+)/([\d.]+)', line)
        if rtt_match:
            stats["min_time"] = float(rtt_match.group(1))
            stats["avg_time"] = float(rtt_match.group(2))
            stats["max_time"] = float(rtt_match.group(3))

    return stats


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ping', methods=['POST'])
def ping_host():
    target = request.form.get('hostname', '').strip()

    # Validate input
    is_valid, result = validate_target(target)
    if not is_valid:
        return render_template('index.html', error=result, target=target)

    target = result
    start_time = time.time()

    try:
        cmd = get_ping_command(target)
        output = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            timeout=20
        )
        raw_output = output.decode('utf-8', errors='replace')
        elapsed = round(time.time() - start_time, 2)

        stats = parse_ping_output(raw_output)

        # Determine status
        if stats["received"] == 0:
            status = "failed"
        elif stats["loss_percent"] > 0:
            status = "partial"
        else:
            status = "success"

        return render_template(
            'index.html',
            result=raw_output,
            stats=stats,
            status=status,
            target=target,
            elapsed=elapsed
        )

    except subprocess.CalledProcessError as e:
        raw_output = e.output.decode('utf-8', errors='replace') if e.output else "فشل تنفيذ الأمر"
        return render_template(
            'index.html',
            result=raw_output,
            error="فشل الاتصال",
            status="failed",
            target=target
        )
    except subprocess.TimeoutExpired:
        return render_template(
            'index.html',
            error="انتهت مهلة الاتصال (20 ثانية)",
            status="timeout",
            target=target
        )
    except Exception as e:
        return render_template(
            'index.html',
            error=f"خطأ غير متوقع: {str(e)}",
            status="error",
            target=target
        )


@app.route('/api/ping', methods=['POST'])
def api_ping():
    """JSON API endpoint for ping."""
    data = request.get_json() or {}
    target = data.get('hostname', '').strip()

    is_valid, result = validate_target(target)
    if not is_valid:
        return jsonify({"success": False, "error": result}), 400

    target = result
    start_time = time.time()

    try:
        cmd = get_ping_command(target)
        output = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            timeout=20
        )
        raw_output = output.decode('utf-8', errors='replace')
        elapsed = round(time.time() - start_time, 2)

        stats = parse_ping_output(raw_output)

        return jsonify({
            "success": True,
            "target": target,
            "output": raw_output,
            "stats": stats,
            "elapsed": elapsed
        })

    except subprocess.CalledProcessError as e:
        return jsonify({
            "success": False,
            "target": target,
            "error": "Ping failed",
            "output": e.output.decode('utf-8', errors='replace') if e.output else None
        }), 500
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Timeout"}), 504
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/validate', methods=['POST'])
def api_validate():
    """Validate hostname without pinging."""
    data = request.get_json() or {}
    target = data.get('hostname', '').strip()

    is_valid, result = validate_target(target)
    return jsonify({
        "valid": is_valid,
        "message": result if not is_valid else "Valid hostname/IP",
        "target": target if is_valid else None
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
