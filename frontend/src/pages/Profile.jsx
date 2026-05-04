import { useState, useEffect } from 'react';
import api from '../api';

function Profile() {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [message, setMessage] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadProfile = async () => {
            try {
                const res = await api.get('/api/profile');
                setName(res.data.name);
                setEmail(res.data.email);
            } catch (err) {
                setError("Ошибка загрузки данных");
            } finally {
                setLoading(false);
            }
        };
        loadProfile();
    }, []);

    const handleUpdateProfile = async (e) => {
        e.preventDefault();
        setMessage(null); setError(null);
        try {
            await api.put('/api/profile', { name, email });
            setMessage("✅ Данные успешно обновлены");
        } catch (err) {
            setError(err.response?.data?.detail || "Ошибка при обновлении данных");
        }
    };

    const handleChangePassword = async (e) => {
        e.preventDefault();
        setMessage(null); setError(null);
        try {
            await api.post('/api/change-password', { 
                old_password: oldPassword, 
                new_password: newPassword 
            });
            setMessage("✅ Пароль успешно изменен");
            setOldPassword(''); setNewPassword('');
        } catch (err) {
            setError(err.response?.data?.detail || "Ошибка при смене пароля");
        }
    };

    if (loading) return <div style={styles.container}>Загрузка...</div>;

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                <div style={{textAlign: 'left'}}>
                    <button onClick={() => window.location.href = '/'} style={styles.backBtn}>← Вернуться на сайт</button>
                </div>
                
                <h2 style={styles.title}>Личный кабинет</h2>

                {message && <div style={styles.successBox}>{message}</div>}
                {error && <div style={styles.errorBox}>{error}</div>}

                <form onSubmit={handleUpdateProfile} style={styles.form}>
                    <div style={styles.inputGroup}>
                        <label style={styles.label}>Электронная почта</label>
                        <input 
                            type="email" 
                            value={email} 
                            onChange={e => setEmail(e.target.value)} 
                            style={styles.input} 
                        />
                    </div>
                    
                    <div style={styles.inputGroup}>
                        <label style={styles.label}>Отображаемое имя</label>
                        <input 
                            type="text" 
                            value={name} 
                            onChange={e => setName(e.target.value)} 
                            style={styles.input} 
                        />
                    </div>
                    
                    <button type="submit" style={styles.mainBtn}>Обновить данные</button>
                </form>

                <div style={styles.divider}>Безопасность</div>

                <form onSubmit={handleChangePassword} style={styles.form}>
                    <input 
                        type="password" 
                        placeholder="Текущий пароль" 
                        value={oldPassword} 
                        onChange={e => setOldPassword(e.target.value)} 
                        style={styles.input} 
                    />
                    <input 
                        type="password" 
                        placeholder="Новый пароль" 
                        value={newPassword} 
                        onChange={e => setNewPassword(e.target.value)} 
                        style={styles.input} 
                    />
                    <button type="submit" style={styles.secondaryBtn}>Сменить пароль</button>
                </form>
            </div>
        </div>
    );
}

const styles = {
    container: { display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f4f7f6', padding: '20px' },
    card: { background: 'white', padding: '40px', borderRadius: '16px', boxShadow: '0 10px 25px rgba(0,0,0,0.05)', width: '100%', maxWidth: '400px', boxSizing: 'border-box', textAlign: 'center' },
    title: { margin: '0 0 25px 0', color: '#1a1a1a', fontSize: '24px', fontWeight: '700', fontFamily: 'Arial' },
    form: { display: 'flex', flexDirection: 'column', gap: '15px' },
    inputGroup: { display: 'flex', flexDirection: 'column', gap: '5px', textAlign: 'left' },
    label: { fontSize: '13px', color: '#666', fontWeight: '600' },
    input: { padding: '12px 16px', borderRadius: '8px', border: '1px solid #dee2e6', fontSize: '15px', outline: 'none' },
    mainBtn: { background: 'linear-gradient(45deg, #007bff, #0056b3)', color: 'white', border: 'none', padding: '14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold', fontSize: '16px', boxShadow: '0 4px 10px rgba(0, 123, 255, 0.2)' },
    secondaryBtn: { background: '#f8f9fa', color: '#495057', border: '1px solid #dee2e6', padding: '12px', borderRadius: '8px', cursor: 'pointer', fontWeight: '600' },
    backBtn: { background: 'none', border: 'none', color: '#007bff', cursor: 'pointer', fontSize: '14px', marginBottom: '15px', padding: 0 },
    divider: { margin: '30px 0 15px', fontSize: '11px', color: '#adb5bd', textTransform: 'uppercase', letterSpacing: '1.5px', fontWeight: '700' },
    errorBox: { background: '#fff5f5', color: '#e03131', padding: '12px', borderRadius: '8px', fontSize: '14px', marginBottom: '20px', border: '1px solid #ffc9c9' },
    successBox: { background: '#ebfbee', color: '#2f9e44', padding: '12px', borderRadius: '8px', fontSize: '14px', marginBottom: '20px', border: '1px solid #b2f2bb' }
};

export default Profile;