# GunnyCam

We need the `<CLIENT ID>` and `<CLIENT SECRET>` from the Amazon Developers Kit
under the Alexa Voice Service. See [1] for more information.

0. Install dependencies:

    ```bash
    ./install.sh
    ```

1. Go to a working directory:

    ```bash
    cd ~/tmp
    tmux new -s cam
    ```

2. Get the authentication code:

    ```bash
    auth_code.sh <DEVICE> <CLIENT ID>
    ```

    Paste the URL into a browser, log in, and grab the string after `code=`.

    See [1].

3. Get the authentication token:

    ```bash
    auth_token.sh <CODE> <CLIENT ID> <CLIENT SECRET>
    ```

## References

[1] https://github.com/gravesjohnr/AlexaNotificationCurl
