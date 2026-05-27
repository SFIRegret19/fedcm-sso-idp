/**
 * Модуль детекции поддержки технологии FedCM
 */

const INCOMPATIBLE_BROWSERS = [
    {
        name: 'Yandex Browser',
        detector: () => {
            if (navigator.userAgent.includes("YaBrowser") || navigator.userAgent.includes("Yandex")) {
                return true;
            }

            if (navigator.userAgentData && navigator.userAgentData.brands) {
                return navigator.userAgentData.brands.some(item => 
                    item.brand.includes("YaBrowser") || item.brand.includes("Yandex")
                );
            }
            return false;
        }
    }
];

export function getFedCmSupportStatus() {
    // 1. Проверка на защищенное соединение
    if (!window.isSecureContext) {
        return { supported: false, reason: 'Требуется HTTPS соединение' };
    }

    // 2. Проверка наличия нативного API
    if (!window.IdentityCredential) {
        return { supported: false, reason: 'API не поддерживается браузером' };
    }

    // 3. Проверка по черному списку (проблемные реализации Chromium)
    for (const browser of INCOMPATIBLE_BROWSERS) {
        if (browser.detector()) {
            return { supported: false, reason: `Экспериментальная поддержка в ${browser.name} временно ограничена` };
        }
    }

    return { supported: true, reason: 'Полная поддержка. OK' };
}