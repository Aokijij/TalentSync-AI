import { useEffect, useRef, useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";

export function useInterviewCall(roomId) {
  const localVideo = useRef(null);
  const remoteVideo = useRef(null);
  const state = useRef(null);
  const [status, setStatus] = useState("Desconectado");
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState("");

  function stop() {
    const current = state.current;
    state.current = null;
    if (current) {
      clearTimeout(current.timer);
      current.pc?.close();
      current.stream?.getTracks().forEach((track) => track.stop());
      if (current.id) api.delete(`/interviews/rooms/${roomId}/participants/${current.id}`).catch(() => {});
    }
    if (localVideo.current) localVideo.current.srcObject = null;
    if (remoteVideo.current) remoteVideo.current.srcObject = null;
    setConnected(false);
    setStatus("Desconectado");
  }

  useEffect(() => () => stop(), [roomId]);

  async function start() {
    if (state.current) return;
    setError("");
    setStatus("Solicitando permiso de cámara y micrófono…");
    const current = { stream: null, id: null, pc: null, peer: null, timer: null, cursor: 0, pendingIce: [] };
    state.current = current;
    try {
      if (!navigator.mediaDevices?.getUserMedia || !window.RTCPeerConnection) throw new Error("Este navegador no permite videollamadas. Usa localhost en un navegador compatible.");
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      if (state.current !== current) { stream.getTracks().forEach((track) => track.stop()); return; }
      current.stream = stream;
      if (localVideo.current) localVideo.current.srcObject = stream;
      const response = await api.post(`/interviews/rooms/${roomId}/connect`);
      current.id = response.data.participant_id;
      if (state.current !== current) { api.delete(`/interviews/rooms/${roomId}/participants/${current.id}`).catch(() => {}); return; }
      setConnected(true);
      setStatus("Esperando al otro participante");

      async function send(kind, payload) {
        if (state.current !== current || !current.peer) return;
        await api.post(`/interviews/rooms/${roomId}/participants/${current.id}/signal`, { recipient_id: current.peer, kind, payload });
      }

      function prepare(peer) {
        current.pc?.close();
        current.pendingIce = [];
        current.peer = peer;
        if (remoteVideo.current) remoteVideo.current.srcObject = null;
        if (!peer) { current.pc = null; setStatus("Esperando al otro participante"); return; }
        // Local connections only: no external STUN/TURN or media relay.
        const pc = new RTCPeerConnection({ iceServers: [] });
        current.pc = pc;
        stream.getTracks().forEach((track) => pc.addTrack(track, stream));
        pc.ontrack = (event) => { if (current.pc === pc && remoteVideo.current) remoteVideo.current.srcObject = event.streams[0]; };
        pc.onicecandidate = (event) => { if (current.pc === pc && event.candidate) send("ice", event.candidate.toJSON()).catch((failure) => setError(getApiErrorMessage(failure))); };
        pc.onconnectionstatechange = () => {
          if (state.current !== current || current.pc !== pc) return;
          setStatus(pc.connectionState === "connected" ? "Videollamada conectada" : pc.connectionState === "failed" ? "No se pudo conectar. Desconecta y vuelve a intentar en la misma red local." : "Conectando navegadores…");
        };
      }

      async function poll() {
        if (state.current !== current) return;
        try {
          const { data } = await api.post(`/interviews/rooms/${roomId}/presence`, { participant_id: current.id, after_id: current.cursor });
          if (state.current !== current) return;
          const peer = data.participants.find((item) => item.id !== current.id)?.id ?? null;
          if (peer !== current.peer) {
            prepare(peer);
            if (peer && current.id < peer) {
              await current.pc.setLocalDescription(await current.pc.createOffer());
              await send("offer", current.pc.localDescription.toJSON());
            }
          }
          for (const signal of data.signals) {
            if (state.current !== current) return;
            current.cursor = Math.max(current.cursor, signal.id);
            if (signal.sender_id !== current.peer || !current.pc) continue;
            const pc = current.pc;
            if (signal.kind === "ice") {
              if (pc.remoteDescription) await pc.addIceCandidate(signal.payload);
              else current.pendingIce.push(signal.payload);
            } else {
              await pc.setRemoteDescription(signal.payload);
              for (const candidate of current.pendingIce.splice(0)) await pc.addIceCandidate(candidate);
              if (signal.kind === "offer") {
                await pc.setLocalDescription(await pc.createAnswer());
                await send("answer", pc.localDescription.toJSON());
              }
            }
          }
        } catch (failure) {
          if (state.current !== current) return;
          setError(getApiErrorMessage(failure, failure.message));
          stop();
          return;
        }
        if (state.current === current) current.timer = setTimeout(poll, 1500);
      }
      poll();
    } catch (failure) {
      if (state.current !== current) return;
      setError(getApiErrorMessage(failure, failure.message));
      stop();
    }
  }

  return { localVideo, remoteVideo, status, connected, error, start, stop };
}
