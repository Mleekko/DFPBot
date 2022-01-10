# Installing DFPBot as a Systemd Service

(These instructions were tested on Ubuntu 20.04 LTS)

1. Create a non-root user to run the DFPBot process

    ```
    useradd -m -s /bin/bash dfpbot
    ```

2. Copy all the DFPBot files into the dfpbot user home directory

    ```
    /home/dfpbot/DFPBot/
    ```

3. Copy the dfpbot.service file into /etc/systemd/system/

    ```
    sudo cp dfpbot.service /etc/systemd/system/
    ```

    The service file is configured to run as the dfpbot user and group and use
    /home/dfpbot/DFPBot as the working directory. You shouldn't need to change any
    configuration values if you've set up the dfpbot user as above.


4. Let systemd know about the new service file by running:

    ```
    sudo systemctl daemon-reload
    ```

5. Start the dfpbot service:

    ```
    sudo systemctl start dfpbot
    ```

6. Check the running status as follows:

    ```
    sudo systemctl status dfpbot
    ```

    You should see something similar to below:

    ```
    ● dfpbot.service - DFPBot Service
     Loaded: loaded (/etc/systemd/system/dfpbot.service; enabled; vendor preset: enabled)
     Active: active (running) since Mon 2021-03-15 17:16:17 UTC; 4s ago
   Main PID: 105129 (python3.9)
      Tasks: 11 (limit: 76859)
     Memory: 97.9M
     CGroup: /system.slice/dfpbot.service
             └─105129 /usr/bin/python /home/dfpbot/DFPBot/DFPBot.py
    ```

7. If the bot runs successfully, then enable the service as follows so that it will automatically start up on server reboot:

    ```
    sudo systemctl enable dfpbot
    ```
