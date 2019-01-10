#!/usr/bin/perl
# prepare data (RealWorld test set) for speaker verification task 

if (@ARGV != 2) {
  print STDERR "Usage: $0 <path-to-audioscantrials> <path-to-data-dir>\n";
  print STDERR "e.g. $0 /export/audioscan_trials data/audioscan_trials\n";
  exit(1);
}

($data_base, $out_dir) = @ARGV;

if (! -d "$out_dir") {
  mkdir($out_dir) or die "Could not create directory $!";
}

open(TRIAL_IN, "<", "$data_base/trials.txt") or die "Could not open the verification trials file $data_base/trials.txt";
open(SPKR, ">", "$out_dir/utt2spk") or die "Could not open the output file $out_dir/utt2spk";
open(WAV, ">", "$out_dir/wav.scp") or die "Could not open the output file $out_dir/wav.scp";
open(TRIAL_OUT, ">", "$out_dir/trials") or die "Could not open the output file $out_dir/trials";

while (<TRIAL_IN>) {
  chomp;
  my ($tar_or_none, $path1, $path2) = split;

  # Create entry for left-hand side of trial
  my $wav = "$data_base/$path1";
  my ($spkr_id, $filename) = split('/', $path1);
  (my $segment = $filename) =~ s/\.[^.]+$//;
  my $utt_id1 = "$spkr_id-$segment";
  print WAV "$utt_id1", " $wav", "\n";
  print SPKR "$utt_id1", " $spkr_id", "\n";

  # Create entry for right-hand side of trial
  my $wav = "$data_base/$path2";
  my ($spkr_id, $filename) = split('/', $path2);
  (my $segment = $filename) =~ s/\.[^.]+$//;
  my $utt_id2 = "$spkr_id-$segment";
  print WAV "$utt_id2", " $wav", "\n";
  print SPKR "$utt_id2", " $spkr_id", "\n";

  my $target = "nontarget";
  if ($tar_or_none eq "1") {
    $target = "target";
  }

  print TRIAL_OUT "$utt_id1 $utt_id2 $target\n";
}

close(SPKR) or die;
close(WAV) or die;
close(TRIAL_OUT) or die;
close(TRIAL_IN) or die;

if (system(
  "utils/utt2spk_to_spk2utt.pl $out_dir/utt2spk >$out_dir/spk2utt") != 0) {
  die "Error creating spk2utt file in directory $out_dir";
}
system("env LC_COLLATE=C utils/fix_data_dir.sh $out_dir");
if (system("env LC_COLLATE=C utils/validate_data_dir.sh --no-text --no-feats $out_dir") != 0) {
  die "Error validating directory $out_dir";
}
