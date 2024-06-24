Набор API-сервисов для системы поиска по видео

# front-end
http://192.144.12.231:8080


## Search API
Docs GET http://192.144.12.231:8080/swagger-ui/index.html

POST http://192.144.12.231:8080/search/combine
Content-Type: application/json

```{
  "query": "Как же мне нравится эта песня",
  "coefficientOfCoincidenceDescriptionUser": 1,
  "minimumPrefixLengthDescriptionUser": 1,
  "maximumNumberOfMatchOptionsDescriptionUser": 50,
  
  "coefficientOfCoincidenceAudio": 0,
  "minimumPrefixLengthAudio": 2,
  "maximumNumberOfMatchOptionsAudio": 50,
  
  "coefficientOfCoincidenceVisual": 0,
  "minimumPrefixLengthVisual": 2,
  "maximumNumberOfMatchOptionsVisual": 50,

  "coefficientOfCoincidenceTag": 1,
  "minimumPrefixLengthTag": 2,
  "maximumNumberOfMatchOptionsTag": 50,

  "boostDescriptionUser": 1.0,
  "boostTranscriptionAudio": 0.0,
  "boostDescriptionVisual": 1.0,
  "boostTags": 1.0,
  "boostEmbeddingAudio": 2.0,
  "boostEmbeddingVisual": 10.0,
  "boostEmbeddingUserDescription": 4.0
}
```



## Index API
POST http://192.144.12.231:8080/index
```{
  "url": "",
  "title": "",
  "description": "",
  "tags": ""
}
```

Удаление дублей по хешу видеоконтента
https://github.com/badma2021/yappi

# Сервисы
### Transcription Service
http://192.144.12.231:8001/docs#/
Порт: 8001
Преобразует речь в текст, что необходимо для анализа содержимого видео.

### OCR Service
http://192.144.12.231:8002/docs#/
Порт: 8002
Извлекает текст из кадров видео

### Embeddings Service
http://192.144.12.231:8003/docs#/
Порт: 8003
Создает векторные представления текстов и кадров из видео для контекстного поиска и сравнения данных.

### Audio Classification Service
http://192.144.12.231:8004/docs#/
Порт: 8004
Классифицирует звуковые события, что помогает в маркировке и анализе аудиофрагментов.
Приоритизации информации для поиска
