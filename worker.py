import os

import pika
import sys
import json


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='PDF_queue')

    def callback(ch, method, props, body: bytes):
        nick = body.decode('utf-8')
        with open(f"{nick}/{nick}.json", 'r') as file:
            data = json.load(file)

        markdown_body = f"####{data['Nick']}\\n" \
                        f"![player avatar]({nick}.png)" \
                        f"Sex: {data['Sex']}" \
                        f"E-mail: {data['E-mail']}" \
                        f"Games: {data['Games']}" \
                        f"Wins: {data['Wins']}" \
                        f"Losses: {data['Losses']}" \
                        f"Time: {data['Time']}"
        with open(f"{nick}/{nick}.md", 'r') as file:
            file.write(markdown_body)
        os.system(f"pandoc {nick}.md -o {nick}/{nick}.pdf")
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id),
                         body="")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='PDF_queue', on_message_callback=callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')

    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Keyboard Interrupt")
        sys.exit(0)
