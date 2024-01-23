close all
clear all
format long

% https://kotetsu1701.com/blog/programing-language-octave/
% Julian Day

function julian = julianDay(year, month, day)
    branch = year + (month - 1.0) / 12.0 + day / 365.25;

    if (floor(month) < 3)
        month = month + 12.0;
        year = year - 1.0;
    endif

    if (branch >= 1582.78)
        julian = floor(year * 365.25) + floor(year / 400.0) - floor(year / 100.0) + floor(30.59 * (month - 2.0)) + day + 1721088.5;
    elseif (branch >= 0.0)
        julian = floor(year * 365.25) + floor(30.59 * (month - 2.0)) + day + 1721086.5;
    elseif (year < 0.0)
        julian = sign(year) * floor(abs(year) * 365.25) + floor(30.59 * (month - 2.0)) + day + 1721085.5;
    end
end

% https://www.epochconverter.com/
unixtime="1704622934"; % 2024/01/07 @ 10:22:14
date1=str2num(unixtime);
tmp=datevec(date1/86400+datenum('1/1/1970','mm/dd/yyyy'));
thedate=julianDay(tmp(1),tmp(2),tmp(3)+(tmp(4)+tmp(5)/60+tmp(6)/3600)/24)-2400000.5-59000
% http://www.csgnetwork.com/julianmodifdateconv.html 1316.432106481399
