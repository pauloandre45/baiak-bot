// BaiakBotDLL.cpp
// DLL que exporta HP/MP do Tibia para o bot Python
// Compila com: cl /LD BaiakBotDLL.cpp /link /OUT:BaiakBot.dll

#include <windows.h>
#include <stdio.h>
#include <stdint.h>

// =====================================================
// CONFIGURACAO - PATTERNS PARA ENCONTRAR HP/MP
// =====================================================

// Estrutura de dados compartilhados
#pragma pack(push, 1)
struct SharedData {
    uint32_t hp;
    uint32_t hp_max;
    uint32_t mp;
    uint32_t mp_max;
    uint64_t timestamp;
    uint32_t player_id;
    uint32_t flags;
};
#pragma pack(pop)

// Nome do shared memory
const char* SHARED_MEMORY_NAME = "BaiakBotSharedMemory";
const char* SHARED_FILE_NAME = "baiak_bot_data.bin";

// Variaveis globais
HANDLE g_hMapFile = NULL;
SharedData* g_pSharedData = NULL;
HANDLE g_hThread = NULL;
volatile bool g_bRunning = true;

// Enderecos encontrados
uintptr_t g_ptrHP = 0;
uintptr_t g_ptrHPMax = 0;
uintptr_t g_ptrMP = 0;
uintptr_t g_ptrMPMax = 0;

// =====================================================
// PATTERN SCANNING
// =====================================================

// Verifica se endereco e valido para leitura
bool IsValidReadPtr(void* ptr, size_t size = 4) {
    MEMORY_BASIC_INFORMATION mbi;
    if (VirtualQuery(ptr, &mbi, sizeof(mbi)) == 0) return false;
    if (mbi.State != MEM_COMMIT) return false;
    if (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) return false;
    return true;
}

// Le int32 seguro
int32_t SafeReadInt(uintptr_t addr) {
    if (!IsValidReadPtr((void*)addr)) return 0;
    __try {
        return *(int32_t*)addr;
    }
    __except(EXCEPTION_EXECUTE_HANDLER) {
        return 0;
    }
}

// Busca pattern na memoria
uintptr_t FindPattern(uintptr_t start, size_t size, const char* pattern, const char* mask) {
    size_t patternLen = strlen(mask);
    
    for (size_t i = 0; i < size - patternLen; i++) {
        bool found = true;
        for (size_t j = 0; j < patternLen; j++) {
            if (mask[j] == 'x' && pattern[j] != ((char*)start)[i + j]) {
                found = false;
                break;
            }
        }
        if (found) return start + i;
    }
    return 0;
}

// Busca valor int32 na memoria
uintptr_t FindValue(uintptr_t start, size_t size, int32_t value) {
    for (size_t i = 0; i < size - 4; i += 4) {
        if (!IsValidReadPtr((void*)(start + i))) continue;
        __try {
            if (*(int32_t*)(start + i) == value) {
                return start + i;
            }
        }
        __except(EXCEPTION_EXECUTE_HANDLER) {}
    }
    return 0;
}

// =====================================================
// SCANNER DE HP/MP
// =====================================================

// Estrutura esperada do player:
// [HP] [HP_MAX] ... (offset 0x620) [MP] [MP_MAX]
// HP + 0x8 = HP_MAX
// HP + 0x620 = MP
// HP + 0x628 = MP_MAX

bool ValidatePlayerStructure(uintptr_t addr) {
    int32_t hp = SafeReadInt(addr);
    int32_t hp_max = SafeReadInt(addr + 0x8);
    int32_t mp = SafeReadInt(addr + 0x620);
    int32_t mp_max = SafeReadInt(addr + 0x628);
    
    // Validacoes
    if (hp <= 0 || hp > 100000) return false;
    if (hp_max <= 0 || hp_max > 100000) return false;
    if (hp > hp_max) return false;
    if (mp < 0 || mp > 500000) return false;
    if (mp_max < 0 || mp_max > 500000) return false;
    if (mp_max > 0 && mp > mp_max) return false;
    
    // HP e HP_MAX devem ser razoavelmente proximos quando HP esta cheio
    // ou HP_MAX deve ser maior que HP
    
    return true;
}

bool ScanForPlayerData() {
    // Escaneia heap do processo
    MEMORY_BASIC_INFORMATION mbi;
    uintptr_t addr = 0x10000;
    uintptr_t maxAddr = 0x7FFFFFFFFFFF;  // 64-bit
    
    int candidatesFound = 0;
    
    while (addr < maxAddr && VirtualQuery((void*)addr, &mbi, sizeof(mbi))) {
        if (mbi.State == MEM_COMMIT && 
            (mbi.Protect & (PAGE_READWRITE | PAGE_READONLY)) &&
            !(mbi.Protect & PAGE_GUARD) &&
            mbi.RegionSize > 0x1000) {
            
            // Escaneia esta regiao
            uintptr_t regionEnd = addr + mbi.RegionSize;
            
            for (uintptr_t ptr = addr; ptr < regionEnd - 0x630; ptr += 4) {
                if (ValidatePlayerStructure(ptr)) {
                    g_ptrHP = ptr;
                    g_ptrHPMax = ptr + 0x8;
                    g_ptrMP = ptr + 0x620;
                    g_ptrMPMax = ptr + 0x628;
                    
                    // Log para debug
                    char msg[256];
                    sprintf_s(msg, "[BaiakBot] Player encontrado @ 0x%llX - HP: %d/%d MP: %d/%d\n",
                        (unsigned long long)ptr,
                        SafeReadInt(g_ptrHP), SafeReadInt(g_ptrHPMax),
                        SafeReadInt(g_ptrMP), SafeReadInt(g_ptrMPMax));
                    OutputDebugStringA(msg);
                    
                    return true;
                }
            }
        }
        
        addr += mbi.RegionSize;
        if (addr == 0) break;  // Overflow
    }
    
    return false;
}

// =====================================================
// SHARED MEMORY
// =====================================================

bool CreateSharedMemory() {
    g_hMapFile = CreateFileMappingA(
        INVALID_HANDLE_VALUE,
        NULL,
        PAGE_READWRITE,
        0,
        sizeof(SharedData),
        SHARED_MEMORY_NAME
    );
    
    if (g_hMapFile == NULL) {
        OutputDebugStringA("[BaiakBot] Falha ao criar shared memory\n");
        return false;
    }
    
    g_pSharedData = (SharedData*)MapViewOfFile(
        g_hMapFile,
        FILE_MAP_ALL_ACCESS,
        0, 0,
        sizeof(SharedData)
    );
    
    if (g_pSharedData == NULL) {
        CloseHandle(g_hMapFile);
        g_hMapFile = NULL;
        OutputDebugStringA("[BaiakBot] Falha ao mapear shared memory\n");
        return false;
    }
    
    ZeroMemory(g_pSharedData, sizeof(SharedData));
    OutputDebugStringA("[BaiakBot] Shared memory criado\n");
    return true;
}

void WriteToFile() {
    char tempPath[MAX_PATH];
    GetTempPathA(MAX_PATH, tempPath);
    strcat_s(tempPath, SHARED_FILE_NAME);
    
    FILE* f = NULL;
    if (fopen_s(&f, tempPath, "wb") == 0 && f) {
        SharedData data;
        data.hp = SafeReadInt(g_ptrHP);
        data.hp_max = SafeReadInt(g_ptrHPMax);
        data.mp = SafeReadInt(g_ptrMP);
        data.mp_max = SafeReadInt(g_ptrMPMax);
        data.timestamp = GetTickCount64();
        data.player_id = 0;
        data.flags = 1;  // Indica dados validos
        
        fwrite(&data, sizeof(data), 1, f);
        fclose(f);
    }
}

// =====================================================
// THREAD PRINCIPAL
// =====================================================

DWORD WINAPI MainThread(LPVOID lpParam) {
    OutputDebugStringA("[BaiakBot] Thread iniciada\n");
    
    // Aguarda cliente estabilizar
    Sleep(2000);
    
    // Escaneia player
    int retries = 0;
    while (g_bRunning && g_ptrHP == 0) {
        if (ScanForPlayerData()) {
            OutputDebugStringA("[BaiakBot] Player encontrado!\n");
            break;
        }
        
        retries++;
        if (retries > 30) {
            OutputDebugStringA("[BaiakBot] Player nao encontrado apos 30 tentativas\n");
            retries = 0;
        }
        
        Sleep(1000);
    }
    
    // Cria shared memory
    if (!CreateSharedMemory()) {
        // Usa arquivo como fallback
        OutputDebugStringA("[BaiakBot] Usando arquivo como fallback\n");
    }
    
    // Loop principal - atualiza dados
    while (g_bRunning) {
        // Verifica se endereco ainda e valido
        if (g_ptrHP && !ValidatePlayerStructure(g_ptrHP)) {
            OutputDebugStringA("[BaiakBot] Estrutura invalida, re-escaneando...\n");
            g_ptrHP = 0;
            
            // Re-escaneia
            for (int i = 0; i < 10 && g_bRunning; i++) {
                if (ScanForPlayerData()) break;
                Sleep(500);
            }
        }
        
        // Atualiza shared memory
        if (g_pSharedData && g_ptrHP) {
            g_pSharedData->hp = SafeReadInt(g_ptrHP);
            g_pSharedData->hp_max = SafeReadInt(g_ptrHPMax);
            g_pSharedData->mp = SafeReadInt(g_ptrMP);
            g_pSharedData->mp_max = SafeReadInt(g_ptrMPMax);
            g_pSharedData->timestamp = GetTickCount64();
            g_pSharedData->flags = 1;
        }
        
        // Tambem escreve em arquivo
        if (g_ptrHP) {
            WriteToFile();
        }
        
        Sleep(50);  // 20 FPS
    }
    
    OutputDebugStringA("[BaiakBot] Thread finalizada\n");
    return 0;
}

// =====================================================
// DLL ENTRY POINT
// =====================================================

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID lpReserved) {
    switch (reason) {
        case DLL_PROCESS_ATTACH:
            DisableThreadLibraryCalls(hModule);
            OutputDebugStringA("[BaiakBot] DLL carregada!\n");
            g_hThread = CreateThread(NULL, 0, MainThread, NULL, 0, NULL);
            break;
            
        case DLL_PROCESS_DETACH:
            g_bRunning = false;
            if (g_hThread) {
                WaitForSingleObject(g_hThread, 3000);
                CloseHandle(g_hThread);
            }
            if (g_pSharedData) UnmapViewOfFile(g_pSharedData);
            if (g_hMapFile) CloseHandle(g_hMapFile);
            OutputDebugStringA("[BaiakBot] DLL descarregada\n");
            break;
    }
    return TRUE;
}

// Exporta funcoes para acesso externo (opcional)
extern "C" {
    __declspec(dllexport) int GetHP() { return SafeReadInt(g_ptrHP); }
    __declspec(dllexport) int GetHPMax() { return SafeReadInt(g_ptrHPMax); }
    __declspec(dllexport) int GetMP() { return SafeReadInt(g_ptrMP); }
    __declspec(dllexport) int GetMPMax() { return SafeReadInt(g_ptrMPMax); }
    __declspec(dllexport) bool IsReady() { return g_ptrHP != 0; }
}
