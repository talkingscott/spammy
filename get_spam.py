"""
Gets spam (Junk) for last N days
"""
import datetime
import email
import email.header
import json
import logging
import traceback

from imapclient import IMAPClient

DEFAULT_ENCODING = 'windows-1252'    # more permissive than us-ascii or iso-8859-1
DECODE_ERRORS = 'backslashreplace'

def _header_string(msg, header_name):
    """ Gets the value of a message header as a string. """
    header_bytes = msg[header_name]
    logging.debug('header_bytes for %s: %r type(header_bytes): %s',
                 header_name, header_bytes, type(header_bytes))
    if header_bytes is None:
        logging.debug('%s: %s', header_name, header_bytes)
        return header_bytes

    decoded = email.header.decode_header(header_bytes)
    logging.debug('decoded %s: %r', header_name, decoded)
    val = ""
    for fragment in decoded:
        if isinstance(fragment[0], str):
            val += fragment[0]
        else:
            val += fragment[0].decode(fragment[1] if fragment[1] else DEFAULT_ENCODING,
                                      DECODE_ERRORS)

    logging.debug('%s: %s', header_name, val)
    return val

def _payload_string(part):
    """ Gets the payload of a part as a string. """
    if part.get_content_maintype() == 'text':
        encoding = part.get_param('charset', DEFAULT_ENCODING)
        return part.get_payload(decode=True).decode(encoding, DECODE_ERRORS)

    payload = part.get_payload()
    if isinstance(payload, list):
        parts = []
        for subpart in payload:
            parts.append(_payload_string(subpart))
        return str(parts)

    return str(payload)

def _write_file(uid, suffix, contents):
    """ Writes contents to a file """
    filename = f'{str(uid)}{suffix}'
    logging.info('Write file %s', filename)
    with open(filename, 'w', encoding='utf-8') as fp:
        try:
            fp.write(str(contents))
        except: # pylint: disable=W0702
            fp.write(traceback.format_exc())

def _parse_message_data(uid, message_data, debug_files):
    """ Parses message data into strings """
    logging.debug('uid: %d type(uid): %s', uid, type(uid))
    logging.debug('type(message_data): %s', type(message_data))
    if debug_files:
        _write_file(uid, '-message-data.txt', message_data)

    msg = email.message_from_bytes(message_data[b'RFC822'])
    logging.debug('type(msg): %s', type(msg))
    if debug_files:
        _write_file(uid, '-rfc822.txt', msg)

    frm = _header_string(msg, 'From')
    subject = _header_string(msg, 'Subject')
    unsubscribe = _header_string(msg, 'List-Unsubscribe')

    plain_part = None
    html_part = None
    for partno, part in enumerate(msg.walk()):
        logging.debug('type(part): %s', type(part))

        content_type = part.get_content_type()
        logging.debug('content_type: %s', content_type)
        if content_type == 'text/plain':
            plain_part = part
        elif content_type == 'text/html':
            html_part = part

        logging.debug('part.get_charset(): %s', part.get_charset())
        logging.debug('charset param: %s', part.get_param('charset', DEFAULT_ENCODING))
        if debug_files:
            _write_file(uid, f'-{partno}.txt', _payload_string(part))

    return {
        'headers': {
            'From': frm,
            'Subject': subject,
            'List-Unsubscribe': unsubscribe
        },
        'parts': {
            'plain': plain_part,
            'html': html_part
        }
    }

def _get_spam_for_n_days(client, n_days, debug_files=False):
    """ Gets spam (Junk) for the last N days """
    resp = client.select_folder('Junk', readonly=True)
    logging.debug('select_folder response: %s', resp)

    n_days_ago = datetime.datetime.now().astimezone() - datetime.timedelta(days=n_days)
    message_ids = client.search(['SINCE', n_days_ago])
    logging.debug('len(message_ids): %d', len(message_ids))

    for uid, message_data in client.fetch(message_ids, 'RFC822').items():
        logging.info('Parse message %d', uid)
        parsed_message = _parse_message_data(uid, message_data, debug_files)

        plain_part = parsed_message['parts']['plain']
        part = plain_part if plain_part else parsed_message['parts']['html']
        if part:
            payload = _payload_string(part)
        else:
            payload = None

        spam_info = {
            'from': parsed_message['headers']['From'],
            'subject': parsed_message['headers']['Subject'],
            'unsubscribe': parsed_message['headers']['List-Unsubscribe'],
            'payload': payload
        }

        _write_file(uid, '.json', json.dumps(spam_info, indent=2))

def _main(host, username, password, days, debug_files=False):
    """ Connects to IMAP server, logs in, and gets spam (Junk) for the last N days """
    with IMAPClient(host, use_uid=True, ssl=True) as client:
        resp = client.login(username, password)
        logging.debug('login response: %s', resp)

        _get_spam_for_n_days(client, days, debug_files)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    with open('config.json', 'r') as FP_CONFIG:
        CONFIG = json.load(FP_CONFIG)
    _main(CONFIG['host'], CONFIG['username'], CONFIG['password'],
          CONFIG['number_of_days'], CONFIG['write_debug_files'])
