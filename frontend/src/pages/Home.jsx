import { useState, useEffect } from 'react';
import api from '../api';

function Home() {
    const [token, setToken] = useState(null);
    const [error, setError] = useState(null);
    const [isFedCmSupported, setIsFedCmSupported] = useState(false);

    useEffect(() => {
        // Проверяем, поддерживает ли браузер FedCM
        if (window.IdentityCredential) {
            setIsFedCmSupported(true);
        }
    },[]);

    const handleFedCMLogin = async () => {
        setError(null);
        try {
            // Запрашиваем авторизацию у браузера
            const credential = await navigator.credentials.get({
                identity: {
                    providers:[{
                        configURL: `${import.meta.env.VITE_API_URL}/fedcm.json`,
                        clientId: "client1234",
                        params: {
                            nonce: "random-nonce-" + Math.random()
                        }
                    }]
                },
                mediation: 'optional' 
            });

            if (credential && credential.token) {
                setToken(credential.token);
                console.log("JWT Token:", credential.token);
            }
        } catch (err) {
            console.error(err);
            if (err.name === 'AbortError' || err.name === 'NotAllowedError') {
                setError("Вход отменен пользователем");
            } else {
                setError(`Ошибка FedCM: ${err.message}. Возможно, вы не авторизованы.`);
            }
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                <h1>Мой Тестовый Сайт (RP)</h1>
                <p>Используйте FedCM для бесшовного входа</p>

                {isFedCmSupported ? (
                    <button onClick={handleFedCMLogin} style={styles.btn}>
                        Быстрый вход (FedCM)
                    </button>
                ) : (
                    <p style={{ color: 'red' }}>Ваш браузер не поддерживает FedCM</p>
                )}

                {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}

                {token && (
                    <div style={styles.result}>
                        <h3 style={{ color: 'green' }}>Успешный вход!</h3>
                        <p>Ваш JWT токен:</p>
                        <textarea readOnly value={token} style={styles.textarea} />
                    </div>
                )}
            </div>
        </div>
    );
}

const styles = {
    container: { display: 'flex', justifyContent: 'center', paddingTop: '100px', fontFamily: 'Arial' },
    card: { background: 'white', padding: '40px', borderRadius: '12px', boxShadow: '0 4px 15px rgba(0,0,0,0.1)', textAlign: 'center', width: '100%', maxWidth: '450px' },
    btn: { background: '#007bff', color: 'white', border: 'none', padding: '12px 24px', borderRadius: '6px', fontSize: '16px', cursor: 'pointer', width: '100%' },
    result: { marginTop: '20px', background: '#e9ecef', padding: '15px', borderRadius: '6px', textAlign: 'left' },
    textarea: { width: '100%', height: '100px', marginTop: '10px', fontSize: '12px' }
};

export default Home;