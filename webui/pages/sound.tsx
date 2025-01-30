import { useEffect, useState, useRef } from 'react';

export default function Home() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioURLs, setAudioURLs] = useState<string[]>([]); // 保存した音声データのURL
  const [audioTexts, setAudioTexts] = useState<string[]>([]); // 保存した音声データのテキスト
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]); // 録音データのチャンクを保持
  const socketRef = useRef<WebSocket | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);

  const analyserFftSite = 2048;
  const silentChunks = useRef(0);
  const silentStat = useRef(false);

  useEffect(() => {
    // WebSocket接続
    const socket = new WebSocket(process.env.NEXT_PUBLIC_WEBSOCKET_URL || '');
    socket.onopen = () => console.log('WebSocket connected');
    socket.onerror = (error) => console.error('WebSocket error:', error);
    socket.onmessage = (event) => {
      console.log('Message received from WebSocket:', event.data);
      setAudioTexts((prev) => [...prev, event.data]);
    };
    socketRef.current = socket;

    return () => {
      socket.close();
    };
  }, []);

  const startRecording = async () => {
    setIsRecording(true);
    audioChunksRef.current = [];

    // マイク入力を取得
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioStreamRef.current = stream;

    // AudioContextを作成して音声データを解析
    const audioContext = new AudioContext();
    audioContextRef.current = audioContext;

    const source = audioContext.createMediaStreamSource(stream); // ストリームからソースを作成

    const analyser = audioContext.createAnalyser(); // 音声解析用ノード
    analyser.fftSize = analyserFftSite; // サンプルサイズ設定
    analyserRef.current = analyser;

    source.connect(analyser);

    initMediaRecorder();
    checkSilence(); // 無音判定を開始
  };

  const initMediaRecorder = () => {
    try {
      if(!audioStreamRef.current) return;

      const mediaRecorder = new MediaRecorder(audioStreamRef.current);
      mediaRecorderRef.current = mediaRecorder;

      // MediaRecorderのイベントを登録
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          console.log('Audio chunk added:', event.data);
        }
      };

      // 録音が停止された際の処理
      mediaRecorder.onstop = () => {
        saveAndSendAudio();
        if(audioStreamRef.current) {
          audioStreamRef.current.getTracks().forEach((track) => track.stop()); // マイクストリーム停止
        }
      };

      // 録音を開始
      mediaRecorder.start();
      console.log('Recording started...');
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  // 定期的に音声エネルギーを取得して無音判定を行う
  const checkSilence = () => {
    const dataArray = new Uint8Array(analyserFftSite); // 音声データを取得するための配列

    if(analyserRef.current) {
      analyserRef.current.getByteFrequencyData(dataArray);
    }
    const sum = dataArray.reduce((a, b) => a + b, 0); // 振幅データの合計値
    console.log('Sum of amplitudes:', sum);
    console.log('Silence chunks:', silentChunks.current);

    const silenceThreshold = 1000; // 無音と判定する閾値 (小さいほど敏感)
    if (sum < silenceThreshold) {
      silentChunks.current++;
    } else {
      silentChunks.current = 0; // 音が聞こえたらリセット
      silentStat.current = true;
    }

// 無音状態が一定時間続いた場合（ここでは2秒間）
    if (silentChunks.current > 20) {
      silentChunks.current = 0;

      if (silentStat.current && mediaRecorderRef.current?.state === 'recording') {
        console.log('Silence detected. Save recording...');
        mediaRecorderRef.current.onstop = async () => {
          console.log('MediaRecorder stopped. Initializing new instance...');
          saveAndSendAudio();
          initMediaRecorder(); // 停止後にのみ新しいインスタンスを作成
          checkSilence(); // 無音判定の再開
        };
        mediaRecorderRef.current.stop();
        silentStat.current = false;
        return;
      }
    }

    // 無音を継続チェック
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      setTimeout(checkSilence, 100); // 100msごとに振幅をチェック
    }
  };

  // 録音を停止する関数
  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    audioContextRef.current?.close();
    setIsRecording(false); // 録音フラグを更新
    console.log('Recording stopped.');
  };

  const saveAndSendAudio = () => {
    // チャンクデータが空でないか確認
    if (audioChunksRef.current.length === 0) {
      console.error('No audio chunks available to process.');
      return;
    }
    console.log('Audio chunks available to process:', audioChunksRef.current.length);

    // チャンクデータを結合して音声データを作成
    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
    // デバッグ: BlobのサイズとURLを確認
    console.log('Blob created:', audioBlob);
    console.log('Blob size:', audioBlob.size);

    const audioURL = URL.createObjectURL(audioBlob);
    console.log('Generated audio URL:', audioURL);

    // ステートに保存（クライアントで再生可能にする）
    setAudioURLs((prev) => [...prev, audioURL]);

    const promise = blobToBase64(audioBlob);
    promise.then((base64Audio) => {
      if(base64Audio) {
        // WebSocket経由で送信
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
          socketRef.current.send(base64Audio); // base64Audio をWebSocketで送信
          console.log('Audio data sent via WebSocket');
        } else {
          console.error('WebSocket is not open');
        }
      }
    });

    console.log('chunks close.');
    // チャンクをリセット
    audioChunksRef.current = [];
  };

  const blobToBase64 = async (blob: Blob): Promise<string | undefined> => {
    const reader = new FileReader();

    return new Promise((resolve, reject) => {
      reader.onload = () => {
        console.log('Encoding audio blob to Base64...');
        resolve(reader.result?.toString().split(",")[1]);
      };

      reader.onerror = function (error) {
        console.error('Error encoding audio blob to Base64:', error);
        reject(error);
      };

      reader.readAsDataURL(blob); // BlobデータをBase64形式に変換
    });
  };

  return (
      <div>
        <h1>音声録音アプリ</h1>
        <button onClick={startRecording} disabled={isRecording}>
          録音開始
        </button>
        <button onClick={stopRecording} disabled={!isRecording}>
          録音停止
        </button>
        <div>
          <h2>録音データ</h2>
          {audioURLs.map((url, index) => (
              <div key={index}>
                <p>録音 #{index + 1}</p>
                <audio controls>
                  <source src={url} type="audio/webm" />
                  お使いのブラウザはオーディオ再生をサポートしていません。
                </audio>

                <div>
                  <textarea
                      value={audioTexts[index] || ''}
                      readOnly
                      style={{width: '100%', height: '100px', marginTop: '10px'}}
                      placeholder="音声に対して変換されたテキストがここに表示されます"
                  />
                </div>
              </div>
          ))}
        </div>
      </div>
  );
}