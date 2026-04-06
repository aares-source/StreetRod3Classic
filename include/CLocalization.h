/////////////////////////////////////////
//
//             Street Rod 3
//
// Copyright (C) Auxiliary Software 2002-2004
//
//
/////////////////////////////////////////


// Localization system
// Provides multi-language support via INI-style language files.
// Language files live at  data/lang/<code>.ini
// Keys use composite "Section.key" format.
//
// Usage:
//   Font_Draw(x, y, col, "%s", TR("Garage.btn_done"));
//   new CButton(TR("Garage.btn_done"), btn_done);


#ifndef __CLOCALIZATION_H__
#define __CLOCALIZATION_H__

#include <string>
#include <unordered_map>


// Translation lookup macro.
// Returns the translated string for the given "Section.key",
// or the key itself when no translation is loaded.
#define TR(key) (CLocalization::Get().Translate(key))


class CLocalization {
public:
    // Meyer's singleton — thread-safe from C++11 onward
    static CLocalization   &Get();

    // Load a language file from data/lang/<sLangCode>.ini.
    // Returns true on success. Clears any previously loaded strings.
    bool        Load(const char *sLangCode);

    // Return the translated string for a "Section.key" composite key.
    // Falls back to sKey itself when the key is not found.
    const char *Translate(const char *sKey) const;

    // Return the currently loaded language code (e.g. "en", "es").
    const char *GetCurrentLang() const { return m_sCurrentLang.c_str(); }

private:
    CLocalization() = default;
    CLocalization(const CLocalization &) = delete;
    CLocalization &operator=(const CLocalization &) = delete;

    std::unordered_map<std::string, std::string> m_strings;
    std::string                                   m_sCurrentLang;
};


#endif  // __CLOCALIZATION_H__
