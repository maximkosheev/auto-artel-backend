-- Создание тестовых сообщений
--INSERT INTO public.chat_chatmessage
--    (telegram_id, reply_to_telegram_id, created, "text", media, viewed, client_id, manager_id)
--    VALUES(0, 0, '', '', ?, false, 0, 0);

INSERT INTO public.chat_chatmessage
    (telegram_id, reply_to_telegram_id, created, "text", media, viewed, client_id, manager_id)
    VALUES(123, NULL, NOW(), 'Hello', NULL, false, 2, NULL);

INSERT INTO public.chat_chatmessage
    (telegram_id, reply_to_telegram_id, created, "text", media, viewed, client_id, manager_id)
    VALUES(NULL, NULL, NOW(), 'Hello', NULL, false, 2, 2);

INSERT INTO public.chat_chatmessage
    (telegram_id, reply_to_telegram_id, created, "text", media, viewed, client_id, manager_id)
    VALUES(NULL, 123, NOW(), 'How are you?', NULL, false, 2, 2);
