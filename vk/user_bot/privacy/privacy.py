from vk.user_bot import dlp, ND


@dlp.register('закрыть сообщения')
def close_mail(nd: ND):
    nd.msg_op(2, str(
        nd.vk('account.setPrivacy', key='mail_send', value='friends')
    ))


@dlp.register('открыть сообщения')
def open_mail(nd: ND):
    nd.msg_op(2, str(
        nd.vk('account.setPrivacy', key='mail_send', value='all')
    ))
