
function createMessageElement(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.is_manager ? 'manager-message' : 'client-message'}`;
    messageDiv.dataset.messageId = message.id;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    if (isMessageDeleted(message)) {
        contentDiv.classList.add('deleted-message');
    }

    if (message.reply_to) {
        const quoteDiv = document.createElement('div');
        quoteDiv.className = 'message-reply-quote';
        quoteDiv.textContent = message.reply_to.text;
        quoteDiv.onclick = (e) => {
            e.stopPropagation();
            scrollToMessage(message.reply_to.id);
        }
        contentDiv.appendChild(quoteDiv);
    }

    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = message.text;
    contentDiv.appendChild(textDiv);

    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    if (isMessageDeleted(message)) {
         timeDiv.textContent = 'удалено ' + message.deleted;
    } else if (isMessageEdited(message)) {
         timeDiv.textContent = 'изменено ' + message.edited;
    } else {
         timeDiv.textContent = message.created;
    }
    contentDiv.appendChild(timeDiv);

    messageDiv.appendChild(contentDiv);

    messageDiv.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        showContextMenu(e, message);
    });

    return messageDiv;
}

function sendMessage() {
    const messageInput = document.getElementById("messageInput");
    const messageText = messageInput.value.trim();

    if (!messageText) {
        return;
    }

    if (editingMessage) {
        send_status = sendToWS({
            action: 'edit_message',
            client_id: selected_client_id,
            message_id: editingMessage.id,
            text: messageText
        });
        if (send_status) {
            cancelEdit();
            messageInput.value = '';
        }
    } else {
        send_status = sendToWS({
            action: 'send_message',
            client_id: selected_client_id,
            text: messageText,
            reply_to_id: replyToMessage ? replyToMessage.id : null
        })
        if (send_status) {
            cancelReply();
            messageInput.value = '';
        }
    }
}

function replayMessage() {
    if (!contextMenuMessage) return;
    if (isMessageDeleted(contextMenuMessage)) {
        showError('Вы не можете ответить на удаленное сообщение');
        return;
    }
    replyToMessage = contextMenuMessage;
    document.getElementById('replyText').textContent = 'В ответ на: ' + truncateText(replyToMessage.text, 50);
    document.getElementById('replyIndicator').classList.add('show');
    document.getElementById('messageInput').focus();
    document.getElementById('contextMenu').classList.remove('show');
}

function editMessage() {
    if (!contextMenuMessage) return;
    editingMessage = contextMenuMessage;

    document.getElementById('editText').textContent = 'Редактирование: ' + truncateText(editingMessage.text, 50);
    document.getElementById('editIndicator').classList.add('show');
    document.getElementById('messageInput').focus();
    document.getElementById('contextMenu').classList.remove('show');
}

function deleteMessage() {
    if (!deletingMessage) return;
    console.log('You have deleted message!')
}

function showError(text) {
    modalDiv = document.getElementById('errorModal');
    modalText = document.getElementById('errorText');

    dialog = new bootstrap.Modal(modalDiv, {keyboard: false});
    modalText.textContent = text
    dialog.show();
}

let yesNoConfirmedHandler = null;

function askForDelete() {
    if (!contextMenuMessage) return
    deletingMessage = contextMenuMessage;

    modalDiv = document.getElementById('yesNoModal');
    modalText = document.querySelector('#yesNoModal div.modal-body')

    dialog = new bootstrap.Modal(modalDiv, {keyboard: false});
    modalText.textContent = 'Данное сообщение будет удалено, в том числе у клиента. Удалить?';
    yesNoConfirmedHandler = deleteMessage;
    dialog.show();
}

function yesNoConfirmed() {
    if (!yesNoConfirmedHandler) return;
    yesNoConfirmedHandler();
}

function handleNewMessage(message) {
    if (selected_client_id == message.client_id) {
        const messageElement = createMessageElement(message);
        messagesContainer.appendChild(messageElement);
        scrollToBottom();
    }
}

function handleEditMessage(message) {
    if (selected_client_id == message.client_id) {
        textDiv = document.querySelector(`[data-message-Id="${message.id}"]>div.message-content>div.message-text`);
        timeDiv = document.querySelector(`[data-message-Id="${message.id}"]>div.message-content>div.message-time`);
        if (textDiv && timeDiv) {
            textDiv.textContent = message.text;
            timeDiv.textContent = 'изменено ' + message.edited;
        }
    }
}

function cancelReply() {
    replyToMessage = null;
    document.getElementById('replyIndicator').classList.remove('show');
}

function cancelEdit() {
    editingMessage = null;
    document.getElementById('messageInput').value = '';
    document.getElementById('editIndicator').classList.remove('show');
    document.getElementById('sendButton').textContent = 'Send';
}

function scrollToMessage(messageId) {
    messageElement = document.querySelector(`[data-message-Id="${messageId}"]`);
    if (messageElement) {
        messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        messageElement.classList.add('highlighted');
        setTimeout(() => {
            messageElement.classList.remove('highlighted');
        }, 1000);
    }
}

function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showContextMenu(event, message) {
    event.stopPropagation();
    contextMenuMessage = message;

    const contextMenu = document.getElementById('contextMenu');
    const replyMenuItem = document.getElementById('replyMenuItem');
    const editMenuItem = document.getElementById('editMenuItem');
    const deleteMenuItem = document.getElementById('deleteMenuItem');

    // Show/hide edit and delete options for manager messages only
    if (message.is_manager) {
        editMenuItem.style.display = 'block';
        deleteMenuItem.style.display = 'block';
    } else {
        if (isMessageDeleted(message)) {
            replyMenuItem.classList.add('disabled');
        } else {
            replyMenuItem.classList.remove('disabled');
        }
        editMenuItem.style.display = 'none';
        deleteMenuItem.style.display = 'none';
    }

    contextMenu.style.left = event.clientX + 'px';
    contextMenu.style.top = event.clientY + 'px';
    contextMenu.classList.add('show');
}

function truncateText(text, maxLen) {
    if (!text) return '';
    if (text.length < maxLen) return text;
    return text.substring(0, maxLen) + '...';
}

function isMessageEdited(message) {
    return message.edited && message.edited.length > 0;
}

function isMessageDeleted(message) {
    return message.deleted && message.deleted.length > 0;
}
