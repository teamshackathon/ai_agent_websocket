package function

import (
	"cloud.google.com/go/speech/apiv1"
	"context"
	"fmt"
	"github.com/gorilla/websocket"
	speechpb "google.golang.org/genproto/googleapis/cloud/speech/v1"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"
)

// グローバルクライアント
var (
	speechClient *speech.Client
	once         sync.Once
)

func getSpeechClient() (*speech.Client, error) {
	var err error
	once.Do(func() {
		ctx := context.Background()
		speechClient, err = speech.NewClient(ctx)
	})
	return speechClient, err
}

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		origin := r.Header.Get("Origin")
		coses := strings.Split(os.Getenv("COSE_ORIGIN"), ",")
		for _, v := range coses {
			// 特定のオリジンのみ許可
			if origin == v {
				return true
			}
		}
		return false
	},
}

func HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println("Upgrade error:", err)
		return
	}
	defer conn.Close()

	log.Println("Connected")

	for {
		_, audioData, err := conn.ReadMessage()
		if err != nil {
			log.Println("Error reading message:", err)
			break
		}

		transcribedText, err := processAudioWithAI(audioData)
		if err != nil {
			log.Println("Error processing audio:", err)
			break
		}
		log.Println("Transcribed text:", transcribedText)

		err = conn.WriteMessage(websocket.TextMessage, []byte(transcribedText))
		if err != nil {
			log.Println("Error sending message:", err)
			break
		}
	}
}

func processAudioWithAI(audioData []byte) (string, error) {

	if len(audioData) < 1000 { // 例: データが小さい場合
		log.Println("Skipping small audio fragment")
		return "", nil
	}
	log.Println("Audio data length:", len(audioData))

	client, err := getSpeechClient()
	if err != nil {
		return "", fmt.Errorf("failed to get client: %v", err)
	}

	config := &speechpb.RecognitionConfig{
		Encoding:        speechpb.RecognitionConfig_WEBM_OPUS,
		SampleRateHertz: 48000,
		LanguageCode:    "ja-JP",
	}

	audio := &speechpb.RecognitionAudio{
		AudioSource: &speechpb.RecognitionAudio_Content{
			Content: audioData,
		},
	}

	req := &speechpb.RecognizeRequest{
		Config: config,
		Audio:  audio,
	}

	ctx := context.Background()
	resp, err := client.Recognize(ctx, req)
	if err != nil {
		return "", fmt.Errorf("failed to recognize speech: %v", err)
	}

	// 認識結果を取得
	for _, result := range resp.Results {
		for _, alt := range result.Alternatives {
			// 最も精度の高い結果を返す
			return alt.Transcript, nil
		}
	}

	// 音声が認識されなかった場合
	log.Println("No result")
	return "", nil
}
