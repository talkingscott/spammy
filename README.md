# Get spam (Junk) from an IMAP server

This python script fetches messages from the Junk folder of an IMAP server, parses them, and writes them to JSON files.  The script is not all that long or complex, but is a little too much to be a good gist.

The script uses the imapclient package rather than the imap module to interact with the server.  I don't know whether that saves much work or code.  It also uses the email package to parse the messages.  I am sure that saves work and code, but I'm not sure I am using the package correctly.  In the end, the script does what I needed it to do.

## Configuration

All configuration is read from a file named config.json.  That includes a clear text password.  Be sure to give the file appropriate permissions.  Here's a sample.

```json
{
    "host": "imap.comcast.net",
    "username": "bigbill6",
    "password": "b1gIsl!ttle",

    "number_of_days": 3,
    "write_debug_files": false
}
```

## Output

Each message is written to a file named UID.json, where UID is a numeric ID associated with the message.  The JSON has four fields, as shown in this example.

```json
{
  "from": "United States Postal Service <central.atendimento@minasbrasil.com.br>",
  "subject": "United States Postal Service ticket #38398",
  "unsubscribe": null,
  "payload": "<html><body></body></html>"
}```

The payload is text/plain if available, falling back to text/html.

## Debug

There is both standard python logging messages and debug files.  You can enable debug files in the config.json file.  You can set the logging level as usual.
