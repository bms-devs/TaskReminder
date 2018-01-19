function sleep-until($future_time) 
{ 
    if ([String]$future_time -as [DateTime]) { 
        if ($(get-date $future_time) -gt $(get-date)) { 
            $sec = [system.math]::ceiling($($(get-date $future_time) - $(get-date)).totalseconds) 
            start-sleep -seconds $sec 
        } 
        else { 
            write-host "You must specify a date/time in the future" 
            return 
        } 
    } 
    else { 
        write-host "Incorrect date/time format" 
    } 
}

$checkHour =  New-Object System.TimeSpan -ArgumentList @(8, 0, 0)

$nextRun = (Get-Date).Date.Add($checkHour)

while ($true) {
	python task_reminder.py conf/user_config.json conf/task_reminder_config.json log
	$nextRun = $nextRun.AddDays(1)
	sleep-until($nextRun)
}