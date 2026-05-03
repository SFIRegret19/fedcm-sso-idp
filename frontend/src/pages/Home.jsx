// frontend/src/pages/Home.jsx
import { useState, useEffect } from 'react';
import api from '../api';
import { getFedCmSupportStatus } from '../utils/browser-support';

function Home() {
    const [authStatus, setAuthStatus] = useState('checking'); // checking, logged-in, logged-out
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);
    const [fedCmStatus, setFedCmStatus] = useState({ supported: false, reason: '' });
    const [error, setError] = useState(null);

    useEffect(() => {
        setFedCmStatus(getFedCmSupportStatus());
        checkSession();
    },[]);

    const checkSession = async () => {
        try {
            const res = await api.get('/api/session-check');
            if (res.data.status === 'logged-in') {
                setAuthStatus('logged-in');
                setUser(res.data.user);
            } else {
                setAuthStatus('logged-out');
            }
        } catch (e) {
            setAuthStatus('logged-out');
        }
    };

    const handleFedCMLogin = async () => {
        setError(null);
        try {
            const credential = await navigator.credentials.get({
                identity: {
                    providers:[{
                        configURL: `${import.meta.env.VITE_API_URL}/fedcm.json`,
                        clientId: "client1234",
                        params: { nonce: "random-nonce-" + Math.random() }
                    }]
                },
                mediation: 'optional'
            });

            if (credential) {
                setToken(credential.token);
            }
        } catch (err) {
            console.error("FedCM Error:", err);
            setError(`Быстрый вход отменен или недоступен. Используйте обычный вход.`);
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                <h1>Демо SSO (Relying Party)</h1>
                
                <div style={styles.statusBox}>
                    Статус: <strong>{authStatus === 'checking' ? '⏳ Проверка...' : (authStatus === 'logged-in' ? `✅ Вошли как ${user?.name}` : '❌ Не авторизованы')}</strong>
                </div>

                <div style={styles.buttonGroup}>
                    {/* Кнопка FedCM появляется ТОЛЬКО если есть сессия и поддержка */}
                    {fedCmStatus.supported && authStatus === 'logged-in' && (
                        <button onClick={handleFedCMLogin} style={{...styles.btn, background: '#28a745'}}>
                            Быстрый вход (FedCM)
                        </button>
                    )}

                    {/* Обычная кнопка входа (Редирект) */}
                    <button onClick={() => window.location.href='/login'} style={styles.btn}>
                        {authStatus === 'logged-in' ? 'Сменить аккаунт (через форму)' : 'Войти через форму'}
                    </button>
                </div>

                {!fedCmStatus.supported && (
                    <p style={styles.infoText}><small>ℹ️ {fedCmStatus.reason}</small></p>
                )}

                {error && <p style={{ color: 'red', marginTop: '15px' }}>{error}</p>}

                {token && (
                    <div style={styles.tokenBox}>
                        <strong>JWT Токен получен:</strong><br/>
                        <code style={{fontSize: '11px', display: 'block', marginTop: '5px'}}>{token}</code>
                    </div>
                )}
            </div>
        </div>
    );
}

const styles = {
    container: { display: 'flex', justifyContent: 'center', paddingTop: '80px', fontFamily: 'Arial, sans-serif' },
    card: { background: 'white', padding: '40px', borderRadius: '12px', boxShadow: '0 4px 15px rgba(0,0,0,0.1)', textAlign: 'center', width: '100%', maxWidth: '450px' },
    statusBox: { margin: '20px 0', padding: '15px', borderRadius: '8px', background: '#f8f9fa', fontSize: '16px' },
    buttonGroup: { display: 'flex', flexDirection: 'column', gap: '12px' },
    btn: { padding: '14px 24px', borderRadius: '8px', border: 'none', color: 'white', background: '#007bff', cursor: 'pointer', fontSize: '16px', fontWeight: 'bold' },
    infoText: { color: '#6c757d', marginTop: '15px' },
    tokenBox: { marginTop: '20px', padding: '15px', background: '#d4edda', borderRadius: '8px', wordBreak: 'break-all', textAlign: 'left', color: '#155724' }
};

export default Home;