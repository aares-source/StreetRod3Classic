/////////////////////////////////////////
//
//             Street Rod 3
//
// Copyright (C) Auxiliary Software 2002-2004
//
//
/////////////////////////////////////////


// Localization system
// Created for multi-language support
//
// Language file format (data/lang/<code>.ini):
//   # comment
//   [Section]
//   key = Translated string
//
// Composite map key: "Section.key"


#include "defs.h"
#include "System.h"
#include "CLocalization.h"


CLocalization &CLocalization::Get()
{
    static CLocalization instance;
    return instance;
}


///////////////////
// Load all strings from data/lang/<sLangCode>.ini
bool CLocalization::Load(const char *sLangCode)
{
    char szPath[256];
    snprintf(szPath, sizeof(szPath), "data/lang/%s.ini", sLangCode);

    FILE *fp = fopen(szPath, "rt");
    if (!fp) {
        writeLog("CLocalization: Could not open '%s', falling back to keys\n", szPath);
        return false;
    }

    m_strings.clear();
    m_sCurrentLang = sLangCode;

    char    szLine[512];
    char    szSection[128];
    szSection[0] = '\0';

    while (fgets(szLine, sizeof(szLine), fp) != NULL) {
        // Strip trailing newline / carriage-return
        char *nl = strpbrk(szLine, "\r\n");
        if (nl) *nl = '\0';

        TrimSpaces(szLine);

        // Skip blank lines and comments
        if (szLine[0] == '\0' || szLine[0] == '#')
            continue;

        // Section header: [SectionName]
        size_t len = strlen(szLine);
        if (szLine[0] == '[' && szLine[len - 1] == ']') {
            szLine[len - 1] = '\0';
            strncpy(szSection, szLine + 1, sizeof(szSection) - 1);
            szSection[sizeof(szSection) - 1] = '\0';
            TrimSpaces(szSection);
            continue;
        }

        // Key = Value pair
        char *eq = strchr(szLine, '=');
        if (eq == NULL || szSection[0] == '\0')
            continue;

        *eq = '\0';
        char *szKey   = szLine;
        char *szValue = eq + 1;
        TrimSpaces(szKey);
        TrimSpaces(szValue);

        if (szKey[0] == '\0')
            continue;

        // Build composite key "Section.key" and store
        std::string compositeKey = std::string(szSection) + "." + szKey;
        m_strings[compositeKey] = szValue;
    }

    fclose(fp);

    writeLog("CLocalization: Loaded %zu strings from '%s'\n",
             m_strings.size(), szPath);
    return true;
}


///////////////////
// Return translated string, or the key itself as fallback
const char *CLocalization::Translate(const char *sKey) const
{
    auto it = m_strings.find(sKey);
    if (it != m_strings.end())
        return it->second.c_str();
    return sKey;
}
