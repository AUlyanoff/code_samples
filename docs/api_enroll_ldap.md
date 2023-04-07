Регистрация по логину и паролю
=
> Ответом об успешной регистрации будет объект настроек монитора ([описание](.)).
* **Метод**: `POST`
* **Путь**: `api/v2/enroll/ldap`
* **Параметры в Headers**:
  * `"Content-Type": "application/json"`
  * `User-Agent: <строка идентификации>`, отвечающая требованиям пакета **user_agents 2.1**, 
     <br>используется для получения os_name, os_version, пример: `Mozilla/5.0 (Linux; Android 11; SM-A750FN) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.116 Mobile Safari/537.36`
* **Параметры в Body ` {json} `**:
```json
{
  "login": "str", 
  "password": "str"
}
```
---
Ответ
-
### Если нет соединения с LDAP-сервером
1. Код состояния ответа: `HTTP 476`
2. Описание ошибки в Body ` {json} `:
```json
{
  "error": "No connection with authentication server"
}
```

### Если превышено максимальное количество ошибок входа.
1. Код состояния ответа: `HTTP 477`
2. Описание ошибки в Body ` {json} `:
```json
{
  "error": "Exceeded maximum number of login errors. Try later."
}
```

### Ошибка LDAP-сервера.
1. Код состояния ответа: `HTTP 478`
2. Описание ошибки в Body ` {json} `:
```json
{
  "error": "<Ошибка, полученная от LDAP-сервера, e.g.: Неверный формат логина. Не указан домен."
}
```

### Неверный логин или пароль.
1. Код состояния ответа: `HTTP 479`
2. Описание ошибки в Body ` {json} `:
```json
{
  "error": "No user or password presented."
}
```

### Иначе выдача настроек монитора
1. Код состояния ответа: `HTTP 200 OK`
2. Объект настроек монитора [(описание)](.) в Body ` {json} `:
```json
{
   "kitId": <Integer id устройства>,
   "mdmServerConnection": {
     "type": "ServerConnection",
     "serverUrl": <String host[:port]>,
     "certificates": [<CertificateDto>]
   },
   "socketServerConnection": {
     "type": "ServerConnection",
     "serverUrl": <String host:port>,
     "certificates": [<CertificateDto>]
   },
   "udpLogUrl": <String>,
   "corporateSims": [<SimCardDto>],
   "workSchedule": [<WorkIntervalDto>]
}
```
